# tests/test_api.py
import unittest
import json
from app import app
from app import db, User, SearchHistory


class WeatherAPITests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        self.client = app.test_client()

        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_register(self):
        response = self.client.post('/register',
                                    json={
                                        'username': 'testuser',
                                        'email': 'test@test.com',
                                        'password': 'testpass123'
                                    }
                                    )
        self.assertEqual(response.status_code, 201)

    def test_login(self):
        # First register a user
        self.client.post('/register',
                         json={
                             'username': 'testuser',
                             'email': 'test@test.com',
                             'password': 'testpass123'
                         }
                         )

        # Then try to login
        response = self.client.post('/login',
                                    json={
                                        'email': 'test@test.com',
                                        'password': 'testpass123'
                                    }
                                    )
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json)

    def test_weather_endpoint(self):
        # Register and login to get token
        self.client.post('/register',
                         json={
                             'username': 'testuser',
                             'email': 'test@test.com',
                             'password': 'testpass123'
                         }
                         )

        login_response = self.client.post('/login',
                                          json={
                                              'email': 'test@test.com',
                                              'password': 'testpass123'
                                          }
                                          )

        token = login_response.json['token']

        # Test weather endpoint
        response = self.client.get('/weather/London',
                                   headers={'Authorization': f'Bearer {token}'}
                                   )
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()