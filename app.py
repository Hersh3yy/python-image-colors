from flask import Flask, request
import cv2
import numpy as np
from sklearn.cluster import KMeans
import json

app = Flask(__name__)

def get_color_palette(image, n_colors):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pixels = image.reshape(-1, 3)
    kmeans = KMeans(n_clusters=n_colors)
    kmeans.fit(pixels)
    colors = kmeans.cluster_centers_
    labels = kmeans.labels_
    label_counts = np.bincount(labels)
    color_percentages = label_counts / len(labels)
    palette = [(colors[i].tolist(), float(percent)) for i, percent in enumerate(color_percentages)]
    return palette

@app.route('/analyze', methods=['POST'])
def analyze():
    nparr = np.frombuffer(request.data, np.uint8)
    img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    palette = get_color_palette(img_np, 10)
    return json.dumps(palette)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)