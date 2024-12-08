# model.py
import pickle
import pandas as pd
import numpy as np


def load_model_and_predict(features_dict):
    """
    Load the model and make predictions

    Args:
        features_dict: Dictionary containing feature values
            {
                'Humidity (%)': float,
                'Wind Speed (m/s)': float,
                'Hour': int,
                'Is_Day': int,
                'Weather_Category': str
            }
    """
    # Load the model data
    with open('model.pkl', 'rb') as f:
        model_data = pickle.load(f)

    model = model_data['model']
    scaler = model_data['scaler']
    feature_columns = model_data['feature_columns']

    # Create a DataFrame with all possible weather categories set to 0
    weather_columns = [col for col in feature_columns if col.startswith('Weather_')]
    features = pd.DataFrame(0, index=[0], columns=feature_columns)

    # Set the basic features
    features['Humidity (%)'] = features_dict['Humidity (%)']
    features['Wind Speed (m/s)'] = features_dict['Wind Speed (m/s)']
    features['Hour'] = features_dict['Hour']
    features['Is_Day'] = features_dict['Is_Day']

    # Set the weather category
    weather_col = f"Weather_{features_dict['Weather_Category']}"
    if weather_col in weather_columns:
        features[weather_col] = 1

    # Scale features
    features_scaled = scaler.transform(features)

    # Make prediction
    prediction = model.predict(features_scaled)

    return prediction[0]


# Example usage
if __name__ == "__main__":
    sample_features = {
        'Humidity (%)': 75,
        'Wind Speed (m/s)': 5.2,
        'Hour': 14,
        'Is_Day': 1,
        'Weather_Category': 'Rain'
    }

    predicted_temp = load_model_and_predict(sample_features)
    print(f"Predicted temperature: {predicted_temp:.1f}°C")