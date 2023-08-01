import json
import unittest
from flask_testing import TestCase
from app import app  # Import the Flask app
import logging

class FlaskAppTest(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app
    
    def setUp(self):
        logging.basicConfig(level=logging.INFO)
        logging.info("Setting up the test case")

    def tearDown(self):
        logging.info("Tearing down the test case")

    def test_hello_world(self):
        response = self.client.get('/test')
        self.assertEqual(response.data, b'Hello, World!')

    def test_analyze_no_file(self):
        response = self.client.post('/analyze')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, b'No file part')

    def test_closest_color_invalid_hex(self):
        response = self.client.get('/closest_color', query_string={'hex': 'invalid'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Invalid hex color code')

    def test_closest_color_no_color(self):
        response = self.client.get('/closest_color')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Please provide r, g and b values')
    
    def test_get_closest_color(self):
        response = self.client.get('/closest_color', query_string={'r': 0, 'g': 0, 'b': 0})
        data = json.loads(response.data.decode())

        # Assert the response status code
        self.assertEqual(response.status_code, 200)

        # Assert that the returned color is what you expect (this will depend on your color database)
        # Here we assume black has the color name 'black'
        self.assertEqual(data['color_name'], 'black')

if __name__ == '__main__':
    unittest.main()
