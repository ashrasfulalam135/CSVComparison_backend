# Use an official Python runtime as a parent image
FROM python:3.9.6

# Set the working directory in the container
WORKDIR /app/backend

# Copy requirment.txt to the container
COPY requirements.txt /app/backend/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the fastapi code to the container
COPY . /app/backend/

# Expose a port
EXPOSE 8000

# Start the fastapi server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]