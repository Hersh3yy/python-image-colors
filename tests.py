import json
import unittest
from flask_testing import TestCase
from your_flask_app_file import app  # Import the Flask app

class FlaskAppTest(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app

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

if __name__ == '__main__':
    unittest.main()
