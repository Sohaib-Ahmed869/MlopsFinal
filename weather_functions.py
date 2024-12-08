# weather_functions.py
import requests
import pandas as pd
import csv
from datetime import datetime
from pathlib import Path


def collect_weather_data():
    """
    Collect weather data for predefined cities
    """
    API_KEY = "a6047597a9ed5b49d8c737d44c5a1f81"
    cities = ['London', 'New York', 'Tokyo', 'Paris', 'Sydney']

    csv_file = 'weather_data.csv'

    # Create or truncate the file
    fieldnames = ['City', 'Temperature (°C)', 'Humidity (%)', 'Wind Speed (m/s)',
                  'Weather Condition', 'Date Time']

    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for city in cities:
            try:
                url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
                response = requests.get(url)

                if response.status_code == 200:
                    weather_data = response.json()
                    current_weather = weather_data['list'][0]

                    dt = datetime.fromtimestamp(current_weather['dt'])
                    formatted_datetime = dt.strftime('%Y-%m-%d %H:%M:%S')

                    data_row = {
                        'City': city,
                        'Temperature (°C)': round(current_weather['main']['temp'], 1),
                        'Humidity (%)': current_weather['main']['humidity'],
                        'Wind Speed (m/s)': round(current_weather['wind']['speed'], 1),
                        'Weather Condition': current_weather['weather'][0]['description'],
                        'Date Time': formatted_datetime
                    }
                    writer.writerow(data_row)
                    print(f"Successfully collected data for {city}")
                else:
                    print(f"Failed to collect data for {city}: {response.status_code}")

            except Exception as e:
                print(f"Error collecting data for {city}: {str(e)}")
                continue

    print("Weather data collection completed")
    return True


def preprocess_weather_data():
    """
    Preprocess the collected weather data
    """
    try:
        # Read the CSV file
        df = pd.read_csv('weather_data.csv')

        # Basic preprocessing steps
        # 1. Handle missing values
        df = df.dropna()

        # 2. Convert datetime string to datetime object
        df['Date Time'] = pd.to_datetime(df['Date Time'])

        # 3. Add new features
        df['Hour'] = df['Date Time'].dt.hour
        df['Day'] = df['Date Time'].dt.day
        df['Month'] = df['Date Time'].dt.month
        df['Year'] = df['Date Time'].dt.year

        # 4. Create time-based features
        df['Is_Day'] = df['Hour'].between(6, 18).astype(int)

        # 5. Weather condition encoding
        df['Weather_Category'] = df['Weather Condition'].map(
            lambda x: 'Rain' if 'rain' in x.lower()
            else 'Clear' if 'clear' in x.lower()
            else 'Clouds' if 'cloud' in x.lower()
            else 'Other'
        )

        # Save preprocessed data
        df.to_csv('processed_weather_data.csv', index=False)
        print("Successfully preprocessed weather data")
        return True

    except Exception as e:
        print(f"Error in preprocessing: {str(e)}")
        return False


if __name__ == "__main__":
    collect_weather_data()
    preprocess_weather_data()