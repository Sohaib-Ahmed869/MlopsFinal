# DAG.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import requests
import subprocess
from pathlib import Path
import csv


def collect_weather_data(**context):
    """
    Task to collect weather data for predefined cities
    """
    API_KEY = "a6047597a9ed5b49d8c737d44c5a1f81"
    cities = ['London', 'New York', 'Tokyo', 'Paris', 'Sydney']

    csv_file = 'weather_data.csv'
    is_new_file = True  # Always start fresh when collecting data

    # Create or truncate the file
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ['City', 'Temperature (°C)', 'Humidity (%)', 'Wind Speed (m/s)',
                      'Weather Condition', 'Date Time']
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

                with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writerow(data_row)

                print(f"Successfully collected data for {city}")
            else:
                print(f"Failed to collect data for {city}: {response.status_code}")

        except Exception as e:
            print(f"Error collecting data for {city}: {str(e)}")
            continue


def preprocess_weather_data(**context):
    """
    Task to preprocess the collected weather data
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
        df['Weather_Category'] = df['Weather Condition'].map(lambda x: 'Rain' if 'rain' in x.lower()
        else 'Clear' if 'clear' in x.lower()
        else 'Clouds' if 'cloud' in x.lower()
        else 'Other')

        # Save preprocessed data
        processed_file = 'processed_weather_data.csv'
        df.to_csv(processed_file, index=False)

        # Track preprocessed data with DVC
        try:
            subprocess.run(['dvc', 'add', processed_file], check=True)
            subprocess.run(['git', 'add', f'{processed_file}.dvc'], check=True)
            subprocess.run(['git', 'commit', '-m', 'Update processed weather data'], check=True)
            subprocess.run(['dvc', 'push'], check=True)
            print("Successfully pushed processed data to DVC")
        except subprocess.CalledProcessError as e:
            print(f"Error in DVC operations for processed data: {e}")

    except Exception as e:
        print(f"Error in preprocessing: {str(e)}")
        raise


# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 12, 8),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

# Create the DAG
dag = DAG(
    'weather_data_pipeline',
    default_args=default_args,
    description='Collect and preprocess weather data',
    schedule_interval=timedelta(hours=1),
    catchup=False
)

# Define tasks
collect_task = PythonOperator(
    task_id='collect_weather_data',
    python_callable=collect_weather_data,
    dag=dag
)

preprocess_task = PythonOperator(
    task_id='preprocess_weather_data',
    python_callable=preprocess_weather_data,
    dag=dag
)

# Set task dependencies
collect_task >> preprocess_task