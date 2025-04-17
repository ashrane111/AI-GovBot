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
# Option 1: Copy index and config into the image (simpler for smaller indexes)
# These paths are relative to the build context (Chatbot root)
COPY src/index /app/src/index
COPY src/main/config.json /app/src/main/config.json 
# Consider using secrets/configmaps instead

# Option 2: Mount index/config via K8s volumes (better for large indexes or frequent updates)
# If using this option, remove the COPY lines above. You'll configure volumes in k8s-deployment.yaml.
# Ensure your application code reads the index/config from the mounted path.

# Copy the necessary source code (relative to build context)
COPY src/backend /app/src/backend
COPY src/main /app/src/main
# Add other necessary src subdirectories if needed (e.g., COPY src/utils /app/src/utils)

# Make port 8000 available
EXPOSE 8000

# Define environment variables if needed (e.g., for config paths if not hardcoded)
# ENV CONFIG_PATH=/app/src/main/config.json
# ENV INDEX_PATH=/app/src/main/index

# Run backend.py using uvicorn when the container launches
# Assumes backend.py is runnable via src.backend.backend
CMD ["python3", "src/backend/services.py"]