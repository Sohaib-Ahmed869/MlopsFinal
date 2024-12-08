# tests/test_api.py
import pytest
import os
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, db, User, SearchHistory


@pytest.fixture(scope='session')
def test_app():
    # Configure test database
    db_path = Path("instance/test.db")
    if db_path.exists():
        os.remove(db_path)

    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test_secret_key'
    })
    return app


@pytest.fixture(scope='function')
def client(test_app):
    with test_app.test_client() as client:
        with test_app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


@pytest.fixture(scope='function')
def test_user(client):
    """Create a test user and return the token"""
    user_data = {
        'username': 'testuser',
        'email': 'test@test.com',
        'password': 'testpass123'
    }

    # Register user
    client.post('/register', json=user_data)

    # Login user
    response = client.post('/login', json={
        'email': user_data['email'],
        'password': user_data['password']
    })

    return response.json['token']


def test_register(client):
    """Test user registration endpoint"""
    response = client.post('/register',
                           json={
                               'username': 'testuser',
                               'email': 'test@test.com',
                               'password': 'testpass123'
                           }
                           )
    assert response.status_code == 201
    assert response.json['message'] == 'Registration successful'


def test_register_duplicate_email(client, test_user):
    """Test registration with duplicate email"""
    response = client.post('/register',
                           json={
                               'username': 'testuser2',
                               'email': 'test@test.com',
                               'password': 'testpass123'
                           }
                           )
    assert response.status_code == 409
    assert 'Email already registered' in response.json['message']


def test_login_success(client, test_user):
    """Test successful login"""
    response = client.post('/login',
                           json={
                               'email': 'test@test.com',
                               'password': 'testpass123'
                           }
                           )
    assert response.status_code == 200
    assert 'token' in response.json
    assert 'username' in response.json


def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post('/login',
                           json={
                               'email': 'wrong@email.com',
                               'password': 'wrongpass'
                           }
                           )
    assert response.status_code == 401


def test_weather_endpoint(client, test_user):
    """Test weather endpoint"""
    response = client.get('/weather/London',
                          headers={'Authorization': f'Bearer {test_user}'}
                          )
    assert response.status_code == 200


def test_weather_endpoint_no_token(client):
    """Test weather endpoint without token"""
    response = client.get('/weather/London')
    assert response.status_code == 401


def test_history_endpoint(client, test_user):
    """Test history endpoint"""
    # First make a weather request
    client.get('/weather/London',
               headers={'Authorization': f'Bearer {test_user}'}
               )

    # Then check history
    response = client.get('/history',
                          headers={'Authorization': f'Bearer {test_user}'}
                          )
    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert len(response.json) > 0


if __name__ == '__main__':
    pytest.main(['-v'])