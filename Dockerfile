# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

ENV PYTHONBUFFERED=1
# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir opencv-python-headless numpy scikit-learn flask flask-cors gunicorn webcolors psycopg2-binary python-dotenv colormath Flask-Testing

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run entrypoint.sh
CMD ["./entrypoint.sh"]