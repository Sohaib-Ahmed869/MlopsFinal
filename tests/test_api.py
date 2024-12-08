# tests/test_api.py
import pytest
from main import app, db, User, SearchHistory


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


def test_register(client):
    response = client.post('/register',
                           json={
                               'username': 'testuser',
                               'email': 'test@test.com',
                               'password': 'testpass123'
                           }
                           )
    assert response.status_code == 201


def test_login(client):
    # First register a user
    client.post('/register',
                json={
                    'username': 'testuser',
                    'email': 'test@test.com',
                    'password': 'testpass123'
                }
                )

    # Then try to login
    response = client.post('/login',
                           json={
                               'email': 'test@test.com',
                               'password': 'testpass123'
                           }
                           )
    assert response.status_code == 200
    assert 'token' in response.json


def test_weather_endpoint(client):
    # Register and login to get token
    client.post('/register',
                json={
                    'username': 'testuser',
                    'email': 'test@test.com',
                    'password': 'testpass123'
                }
                )

    login_response = client.post('/login',
                                 json={
                                     'email': 'test@test.com',
                                     'password': 'testpass123'
                                 }
                                 )

    token = login_response.json['token']

    # Test weather endpoint
    response = client.get('/weather/London',
                          headers={'Authorization': f'Bearer {token}'}
                          )
    assert response.status_code == 200