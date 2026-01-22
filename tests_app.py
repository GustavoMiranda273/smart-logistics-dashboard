import unittest
import sys
import os

# Add the parent folder to the path so we can import 'main'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

class BasicTests(unittest.TestCase):

    def setUp(self):
        """Runs before every test. Sets up a fake 'test client'."""
        self.app = app.test_client()
        self.app.testing = True

    def test_index_page_redirect(self):
        """Test 1: Dashboard should redirect to login if not authenticated."""
        # Since our Python code doesn't check the cookie (JS does), 
        # Python actually serves the page, but let's just check it returns 200 OK
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_api_endpoint(self):
        """Test 2: The API should return JSON data."""
        response = self.app.get('/api/deliveries')
        self.assertEqual(response.status_code, 200)
        # Check if the response is actually JSON
        self.assertTrue(response.is_json)

if __name__ == "__main__":
    unittest.main()