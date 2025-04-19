# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the main requirements file from the src directory (relative to build context)
COPY src/requirements.txt /app/

# Install any needed packages specified in requirements.txt
# Add --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# --- Handling the FAISS index and config ---
COPY src/index /app/src/index

# Copy the necessary source code (relative to build context)
COPY src/backend /app/src/backend
COPY src/main /app/src/main

# Make port 8000 available
EXPOSE 8000

# Run backend.py using uvicorn when the container launches
CMD ["python3", "src/backend/services.py"]