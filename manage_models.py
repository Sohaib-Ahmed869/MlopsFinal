# manage_models.py
import mlflow
from mlflow.tracking import MlflowClient
import sys


def list_models():
    """List all registered models and their versions"""
    client = MlflowClient()
    for rm in client.search_registered_models():
        print(f"\nModel: {rm.name}")
        for mv in client.search_model_versions(f"name='{rm.name}'"):
            print(f"  Version {mv.version} - Stage: {mv.current_stage}")


def transition_model(version_id, stage):
    """Transition a model version to a new stage"""
    client = MlflowClient()
    client.transition_model_version_stage(
        name="weather_prediction_model",
        version=version_id,
        stage=stage
    )
    print(f"Transitioned version {version_id} to {stage}")


def compare_models(version1, version2):
    """Compare metrics between two model versions"""
    client = MlflowClient()

    def get_metrics(version):
        run_id = client.get_model_version(
            name="weather_prediction_model",
            version=version
        ).run_id
        run = client.get_run(run_id)
        return run.data.metrics

    metrics1 = get_metrics(version1)
    metrics2 = get_metrics(version2)

    print(f"\nComparison between version {version1} and {version2}:")
    for metric in metrics1:
        if metric in metrics2:
            diff = metrics2[metric] - metrics1[metric]
            print(f"{metric}:")
            print(f"  V{version1}: {metrics1[metric]:.4f}")
            print(f"  V{version2}: {metrics2[metric]:.4f}")
            print(f"  Diff: {diff:.4f}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Available commands:")
        print("  list - List all models and versions")
        print("  promote <version_id> <stage> - Promote model to stage")
        print("  compare <version1> <version2> - Compare two model versions")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        list_models()
    elif command == "promote" and len(sys.argv) == 4:
        transition_model(sys.argv[2], sys.argv[3])
    elif command == "compare" and len(sys.argv) == 4:
        compare_models(sys.argv[2], sys.argv[3])
    else:
        print("Invalid command or arguments")