# Importing required libraries
from flask import Flask, request
from flask_cors import CORS
import cv2
import numpy as np
from sklearn.cluster import KMeans
import json
import webcolors
from color_lookup import parent_colors

# Instantiating Flask app
app = Flask(__name__)
CORS(app)

# Defining parent colors for named colors (this is a simplified version, expand according to your needs)
PARENT_COLORS = {
    'black': 'black',
    'silver': 'grey',
    'gray': 'grey',
    'white': 'white',
    'maroon': 'red',
    'red': 'red',
    'purple': 'purple',
    'fuchsia': 'pink',
    'green': 'green',
    'lime': 'green',
    'olive': 'green',
    'yellow': 'yellow',
    'navy': 'blue',
    'blue': 'blue',
    'teal': 'aqua',
    'aqua': 'aqua'
    # Add more colors
}

# Function to find the closest CSS3 named color for an RGB color
def closest_color(requested_color):
    min_colors = {}
    # For each named color
    for name, hex_color in webcolors.CSS3_NAMES_TO_HEX.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(hex_color)
        # Calculate Euclidean distance from the requested color
        rd = (r_c - requested_color[0]) ** 2
        gd = (g_c - requested_color[1]) ** 2
        bd = (b_c - requested_color[2]) ** 2
        min_colors[(rd + gd + bd)] = name
    # Return the name of the color with the smallest distance
    closest_name = min_colors[min(min_colors.keys())]

    min_parent_colors = {}
    for color in parent_colors:
        hex_color, name = color
        r_c, g_c, b_c = webcolors.hex_to_rgb('#'+hex_color)
        rd = (r_c - requested_color[0]) ** 2
        gd = (g_c - requested_color[1]) ** 2
        bd = (b_c - requested_color[2]) ** 2
        min_parent_colors[(rd + gd + bd)] = name
    closest_parent_name = min_parent_colors[min(min_parent_colors.keys())]

    return closest_name, closest_parent_name

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
        color_name, color_parent = closest_color([int(c) for c in color_rgb])
        color_parent = PARENT_COLORS.get(color_name, 'undefined')
        color_info = {
            'r': int(color_rgb[0]),
            'g': int(color_rgb[1]),
            'b': int(color_rgb[2]),
            'html_code': color_hex,
            'closest_palette_color': color_name,
            'closest_palette_color_parent': color_parent,
            'percent': percent*100,
        }
        palette.append(color_info)
    return palette

# Defining route for color analysis
@app.route('/analyze', methods=['POST'])
def analyze():
    # check if the post request has the file part
    if 'image' not in request.files:
        return 'No file part', 400
    file = request.files['image']

    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return 'No selected file', 400

    if file:
        # Read the file as bytes
        filestr = file.read()

        # Convert the bytes to a numpy array
        npimg = np.frombuffer(filestr, np.uint8)
        # Convert the data to an image
        img_np = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        # Get the color palette
        palette = get_color_palette(img_np, 10)
        # Return the palette as a JSON response
        return json.dumps(palette)

# Main function to run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
