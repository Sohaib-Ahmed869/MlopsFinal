# tests/conftest.py
import pytest
import os
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after adding to path
from main import app, db


@pytest.fixture(scope='session')
def test_app():
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