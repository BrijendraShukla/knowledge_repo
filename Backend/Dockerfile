# Stage 1: Build the Django application
FROM python:3.11.5 as builder

WORKDIR /app

# Copy the requirements file and install the dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the Django port
EXPOSE 8000

# Run Django's development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]