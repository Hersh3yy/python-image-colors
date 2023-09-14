# Importing required libraries
from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
from sklearn.cluster import KMeans
import json
import webcolors
import logging
import time
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import os
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color


load_dotenv()  # take environment variables from .env.


logging.basicConfig(level=logging.INFO)

# Instantiating Flask app
app = Flask(__name__)
CORS(app)

def rgb_to_cmyk(r, g, b):
    logging.info(f'RGB values received: {r}, {g}, {b}')

    r = r / 255.0
    g = g / 255.0
    b = b / 255.0

    k = 1 - max(r, g, b)
    c = (1 - r - k) / (1 - k) if k != 1 else 0
    m = (1 - g - k) / (1 - k) if k != 1 else 0
    y = (1 - b - k) / (1 - k) if k != 1 else 0

    c, m, y, k = [x * 100 for x in [c, m, y, k]]

    logging.info(f'CMYK values calculated: {c}, {m}, {y}, {k}')
    
    return c, m, y, k

# Function to get color palette from image
def get_color_palette(image, n_colors):
    # If the image has an alpha (transparency) channel, filter out transparent pixels
    if image.shape[2] == 4:
        logging.info('transparent image possibly being analyzed...')
        non_transparent_pixels = image[:, :, 3] > 30
        
        alpha_values = image[:, :, 3]
        logging.info(f"Alpha channel min value: {np.min(alpha_values)}, max value: {np.max(alpha_values)}")
        
        # Filter out the transparent pixels before converting to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        non_transparent_rgb_pixels = image_rgb[non_transparent_pixels]

    else:
        # Resize the image
        image_rgb = cv2.resize(image, (700, 700))
        image_rgb = cv2.cvtColor(image_rgb, cv2.COLOR_BGR2RGB)
        non_transparent_rgb_pixels = image_rgb.reshape(-1, 3)

    # Perform KMeans to find the most dominant colors
    kmeans = KMeans(n_clusters=n_colors, n_init=9)
    kmeans.fit(non_transparent_rgb_pixels)
    
    # Get the RGB values of the cluster centers
    colors = kmeans.cluster_centers_

    # Get the labels for all pixels
    labels = kmeans.labels_

    # Count the occurrence of each label
    label_counts = np.bincount(labels)
    total_count = np.sum(label_counts)

    # Calculate the percentage of each color
    color_percentages = label_counts / total_count

    # Prepare the color palette
    palette = []
    for i, percent in enumerate(color_percentages):
        color_rgb = colors[i].tolist()
        color_hex = webcolors.rgb_to_hex([int(c) for c in color_rgb])
        color_info = {
            'r': int(color_rgb[0]),
            'g': int(color_rgb[1]),
            'b': int(color_rgb[2]),
            'html_code': color_hex,
            'percent': percent*100,
        }
        palette.append(color_info)
    return palette

# Defining route for color analysis


@app.route('/analyze', methods=['POST'])
def analyze():
    logging.info('Starting analysis...')
    start_time = time.time()

    # check if the post request has the file part
    if 'image' not in request.files:
        return 'No file part', 400
    file = request.files['image']

    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return 'No selected file', 400

    if file:
        file_start_time = time.time()
        logging.info('Reading the file...')

        # Read the file as bytes
        filestr = file.read()
        logging.info(
            f'Reading the file took: {time.time() - file_start_time} seconds')

        # Convert the bytes to a numpy array
        npimg = np.frombuffer(filestr, np.uint8)

        # Convert the data to an image
        img_np = cv2.imdecode(npimg, cv2.IMREAD_UNCHANGED)

        # Get the color palette
        palette = get_color_palette(img_np, 10)

        # Return the palette as a JSON response
        logging.info(f'Entire request took: {time.time() - start_time} seconds')
        return json.dumps(palette)

@app.route('/closest_color_cmyk', methods=['GET'])
def get_closest_color_cmyk():
    logging.info('Starting closest color CMYK query...')
    start_time = time.time()

    r = request.args.get('r', type=int)
    g = request.args.get('g', type=int)
    b = request.args.get('b', type=int)
    if r is None or g is None or b is None:
        hexCode = request.args.get('hex')
        if hexCode is None:
            return jsonify({"error": "Please provide r, g, and b values"}), 400
        try:
            r, g, b = webcolors.hex_to_rgb("#" + hexCode)
        except ValueError:
            return jsonify({"error": "Invalid hex color code"}), 400

    # Convert RGB to CMYK
    c, m, y, k = rgb_to_cmyk(r, g, b)
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Update the SQL command to compare the CMYK values
    cur.execute("""
        SELECT 
            color_names_cmyk.color_name, 
            color_names_cmyk.hex, 
            color_names_cmyk.cmyk <-> CUBE(array[%s,%s,%s,%s]) as distance, 
            parent_colors_cmyk.color_name as parent_color_name, 
            parent_colors_cmyk.hex as parent_color_hex
        FROM color_names_cmyk
        JOIN parent_colors_cmyk ON color_names_cmyk.parent_color_id = parent_colors_cmyk.id
        ORDER BY distance
        LIMIT 1;
    """, (c, m, y, k))

    result = cur.fetchone()
    logging.info(f'Result from the database: {result}')

    cur.close()
    conn.close()

    logging.info(f'Entire request took: {time.time() - start_time} seconds')
    return jsonify(dict(result))
                

@app.route('/closest_color_lab', methods=['GET'])
def get_closest_color():
    logging.info('Starting closest color lab query...')
    start_time = time.time()

    r = request.args.get('r', type=int)
    g = request.args.get('g', type=int)
    b = request.args.get('b', type=int)
    if r is None or g is None or b is None:
        hexCode = request.args.get('hex')
        if hexCode is None:
            return jsonify({"error": "Please provide r, g and b values"}), 400
        try:
            r, g, b = webcolors.hex_to_rgb("#"+hexCode)
        except ValueError:
            return jsonify({"error": "Invalid hex color code"}), 400

    # Convert RGB to LAB
    rgb = sRGBColor(r, g, b, is_upscaled=True)
    lab = convert_color(rgb, LabColor)

    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Update the SQL command to compare the LAB values
    cur.execute("""
        SELECT 
            color_names_cmyk.color_name, 
            color_names_cmyk.hex, 
            color_names_cmyk.lab <-> CUBE(array[%s,%s,%s]) as distance, 
            parent_colors_cmyk.color_name as parent_color_name, 
            parent_colors_cmyk.hex as parent_color_hex
        FROM color_names_cmyk
        JOIN parent_colors_cmyk ON color_names_cmyk.parent_color_id = parent_colors_cmyk.id
        ORDER BY distance
        LIMIT 1;
    """, (lab.lab_l, lab.lab_a, lab.lab_b))

    result = cur.fetchone()
    cur.close()
    conn.close()

    logging.info(f'Entire request took: {time.time() - start_time} seconds')
    return jsonify(dict(result))


@app.route('/closest_color_rgb', methods=['GET'])
def get_closest_color_rgb():
    logging.info('Starting closest color rgb query...')
    start_time = time.time()

    r = request.args.get('r', type=int)
    g = request.args.get('g', type=int)
    b = request.args.get('b', type=int)
    if r is None or g is None or b is None:
        hexCode = request.args.get('hex')
        if hexCode is None:
            return jsonify({"error": "Please provide r, g and b values"}), 400
        try:
            r, g, b = webcolors.hex_to_rgb("#"+hexCode)
        except ValueError:
            return jsonify({"error": "Invalid hex color code"}), 400

    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT 
            color_names_rgb.color_name, 
            color_names_rgb.hex, 
            color_names_rgb.rgb <-> CUBE(array[%s,%s,%s]) as distance, 
            parent_colors_rgb.color_name as parent_color_name, 
            parent_colors_rgb.hex as parent_color_hex
        FROM color_names_rgb
        JOIN parent_colors_rgb ON color_names_rgb.parent_color_id = parent_colors_rgb.id
        ORDER BY distance
        LIMIT 1;
    """, (r, g, b))

    result = cur.fetchone()
    cur.close()
    conn.close()

    logging.info(f'Entire request took: {time.time() - start_time} seconds')
    return jsonify(dict(result))


@app.route('/test', methods=['GET'])
def test():
    return 'Hello, World!'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
