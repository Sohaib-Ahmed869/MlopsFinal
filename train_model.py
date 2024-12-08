# train_model.py
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import pickle
import yaml
import mlflow
import mlflow.sklearn
from pathlib import Path
import os

# Set MLflow tracking to local directory
mlflow.set_tracking_uri("file:./mlruns")


def evaluate_model(model, X, y, stage=""):
    """Calculate model metrics"""
    predictions = model.predict(X)
    mse = mean_squared_error(y, predictions)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y, predictions)
    r2 = r2_score(y, predictions)

    return {
        f"{stage}_rmse": rmse,
        f"{stage}_mae": mae,
        f"{stage}_r2": r2
    }


def train_weather_model():
    # Load parameters from params.yaml
    with open("params.yaml", 'r') as f:
        params = yaml.safe_load(f)

    # Read preprocessed data
    df = pd.read_csv('processed_weather_data.csv')

    # Create dummy variables for Weather_Category
    weather_dummies = pd.get_dummies(df['Weather_Category'], prefix='Weather')

    # Drop the original Weather_Category column and concatenate dummy variables
    df = df.drop('Weather_Category', axis=1)
    df = pd.concat([df, weather_dummies], axis=1)

    # Prepare features and target
    feature_columns = [
                          'Humidity (%)',
                          'Wind Speed (m/s)',
                          'Hour',
                          'Is_Day'
                      ] + list(weather_dummies.columns)

    X = df[feature_columns]
    y = df['Temperature (°C)']

    # Create or get MLflow experiment
    experiment = mlflow.set_experiment("weather_prediction")

    # Start MLflow run
    with mlflow.start_run(experiment_id=experiment.experiment_id):
        # Log parameters
        mlflow.log_params({
            "test_size": params['train']['test_size'],
            "random_state": params['train']['random_state'],
            "model_type": params['model']['type']
        })

        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=params['train']['test_size'],
            random_state=params['train']['random_state']
        )

        # Scale the features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train the model
        model = LinearRegression()
        model.fit(X_train_scaled, y_train)

        # Calculate and log metrics
        train_metrics = evaluate_model(model, X_train_scaled, y_train, "train")
        test_metrics = evaluate_model(model, X_test_scaled, y_test, "test")

        # Log all metrics to MLflow
        mlflow.log_metrics(train_metrics)
        mlflow.log_metrics(test_metrics)

        # Log feature importance
        feature_importance = pd.DataFrame({
            'Feature': feature_columns,
            'Importance': np.abs(model.coef_)
        })
        feature_importance = feature_importance.sort_values('Importance', ascending=False)

        # Save feature importance plot
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 6))
        plt.barh(feature_importance['Feature'], feature_importance['Importance'])
        plt.title('Feature Importance')
        plt.tight_layout()

        # Save plot and log as artifact
        plt.savefig('feature_importance.png')
        mlflow.log_artifact('feature_importance.png')

        # Save the model
        mlflow.sklearn.log_model(
            model,
            "model",
            registered_model_name="weather_prediction_model"
        )

        # Save the model data locally for DVC
        model_data = {
            'model': model,
            'scaler': scaler,
            'feature_columns': feature_columns
        }
        with open('model.pkl', 'wb') as f:
            pickle.dump(model_data, f)

        # Save metrics for DVC
        metrics = {**train_metrics, **test_metrics}
        with open('metrics.yaml', 'w') as f:
            yaml.dump(metrics, f)

        run_id = mlflow.active_run().info.run_id
        print(f"Model trained successfully. Run ID: {run_id}")
        print(f"Test RMSE: {test_metrics['test_rmse']:.4f}")
        print(f"Test R²: {test_metrics['test_r2']:.4f}")
        print(f"\nMLflow UI: View results by running 'mlflow ui' and opening http://localhost:5000")


if __name__ == "__main__":
    train_weather_model()