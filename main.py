# app.py
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import requests
import os
import csv
import json
import subprocess
from pathlib import Path

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Configuration
app.config['SECRET_KEY'] = 'secret'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)


# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


# Weather Search History Model
class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    searched_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


# Create all database tables
with app.app_context():
    db.create_all()


# Authentication decorator
def token_required(f):
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except:
            return jsonify({'message': 'Token is invalid'}), 401

        return f(current_user, *args, **kwargs)

    decorated.__name__ = f.__name__
    return decorated


# Routes
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

        if not data or not data.get('email') or not data.get('password') or not data.get('username'):
            return jsonify({'message': 'Missing required fields'}), 400

        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already registered'}), 409

        if User.query.filter_by(username=data['username']).first():
            return jsonify({'message': 'Username already taken'}), 409

        # Use 'pbkdf2:sha256' method instead of 'sha256'
        hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')

        new_user = User(
            username=data['username'],
            email=data['email'],
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'Registration successful'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Registration failed: {str(e)}'}), 500


@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Missing email or password'}), 400

        user = User.query.filter_by(email=data['email']).first()

        if user and check_password_hash(user.password, data['password']):
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm="HS256")

            return jsonify({
                'token': token,
                'username': user.username
            })

        return jsonify({'message': 'Invalid credentials'}), 401

    except Exception as e:
        return jsonify({'message': f'Login failed: {str(e)}'}), 500



def save_to_csv_and_push(weather_data, city, user_id):
    """
    Save weather data to CSV and push to DVC remote
    """
    csv_file = 'weather_data.csv'
    is_new_file = not Path(csv_file).exists()

    # Extract current weather data
    current_weather = weather_data['list'][0]
    dt = datetime.datetime.fromtimestamp(current_weather['dt'])
    formatted_datetime = dt.strftime('%Y-%m-%d %H:%M:%S')

    data_row = {
        'City': city,
        'Temperature (°C)': round(current_weather['main']['temp'], 1),
        'Humidity (%)': current_weather['main']['humidity'],
        'Wind Speed (m/s)': round(current_weather['wind']['speed'], 1),
        'Weather Condition': current_weather['weather'][0]['description'],
        'Date Time': formatted_datetime
    }

    # Write to CSV file
    with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=data_row.keys())
        if is_new_file:
            writer.writeheader()
        writer.writerow(data_row)

    try:
        # Update DVC tracking and push to remote
        subprocess.run(['dvc', 'add', csv_file], check=True)
        subprocess.run(['git', 'add', f'{csv_file}.dvc'], check=True)
        subprocess.run(['git', 'commit', '-m', f'Update weather data for {city}'], check=True)
        subprocess.run(['dvc', 'push'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error in DVC operations: {e}")


@app.route('/weather/<city>', methods=['GET'])
@token_required
def get_weather(current_user, city):
    API_KEY = "a6047597a9ed5b49d8c737d44c5a1f81"
    try:
        # Save search history
        search = SearchHistory(user_id=current_user.id, city=city)
        db.session.add(search)
        db.session.commit()

        url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url)

        if response.status_code == 200:
            weather_data = response.json()
            save_to_csv_and_push(weather_data, city, current_user.id)
            return jsonify(weather_data)
        else:
            return jsonify({
                "error": "Failed to fetch weather data ok",
                "status_code": response.status_code
            }), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/history', methods=['GET'])
@token_required
def get_history(current_user):
    searches = SearchHistory.query.filter_by(user_id=current_user.id) \
        .order_by(SearchHistory.searched_at.desc()) \
        .limit(10) \
        .all()

    history = [{
        'city': search.city,
        'searched_at': search.searched_at.strftime("%Y-%m-%d %H:%M:%S")
    } for search in searches]

    return jsonify(history)


if __name__ == '__main__':
    app.run(debug=True, port=5000)