# run_dag_task.py
from weather_functions import collect_weather_data, preprocess_weather_data

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Please specify task: collect_data or preprocess_data")
        sys.exit(1)

    task = sys.argv[1]

    if task == "collect_data":
        success = collect_weather_data()
        if not success:
            sys.exit(1)
    elif task == "preprocess_data":
        success = preprocess_weather_data()
        if not success:
            sys.exit(1)
    else:
        print(f"Unknown task: {task}")
        sys.exit(1)