# Use a Python base image
FROM python:3.8-slim

# Install Tesseract OCR, ImageMagick, and other dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    imagemagick \
    libmagickwand-dev \
    && apt-get clean

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt .

# Copy the policy.xml file to the container
COPY policy.xml /etc/ImageMagick-6/policy.xml

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask app code to the container
COPY . .

# Expose the port the Flask app will run on
EXPOSE 8080

# Set the environment variable for Flask
ENV FLASK_APP=wsgi.py

# Run the Flask app on port 8080
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]
