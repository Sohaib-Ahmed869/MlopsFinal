# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Create volume for SQLite database
VOLUME ["/app/instance"]

EXPOSE 5000

CMD ["python", "app.py"]