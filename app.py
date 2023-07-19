# Importing required libraries
from flask import Flask, request
from flask_cors import CORS
import cv2
import numpy as np
from sklearn.cluster import KMeans
import json
import webcolors
import logging
import time


logging.basicConfig(level=logging.INFO)

# Instantiating Flask app
app = Flask(__name__)
CORS(app)

# Function to get color palette from image
def get_color_palette(image, n_colors):
    # Convert image from BGR to RGB color space
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Reshape the image to be a list of RGB pixels
    pixels = image.reshape(-1, 3)

    # Perform KMeans to find the most dominant colors
    kmeans = KMeans(n_clusters=n_colors, n_init=10)
    kmeans.fit(pixels)
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
        logging.info(f'Reading the file took: {time.time() - file_start_time} seconds')

        # Convert the bytes to a numpy array
        npimg = np.frombuffer(filestr, np.uint8)

        # Convert the data to an image
        img_np = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        # Get the color palette
        palette = get_color_palette(img_np, 10)

        # Return the palette as a JSON response
        logging.info(f'Entire request took: {time.time() - start_time} seconds')
        return json.dumps(palette)

@app.route('/test', methods=['GET'])
def test():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
