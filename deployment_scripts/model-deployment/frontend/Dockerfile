# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the main requirements file from the src directory (relative to build context)
# Consider a separate, smaller requirements.txt specific to the frontend if possible
COPY src/requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the frontend source code (relative to build context)
COPY src/frontend /app/src/frontend
# Copy frontend config if separate
# COPY src/frontend/frontend_config.json /app/src/frontend/frontend_config.json

# Make port 8501 available (default Streamlit port)
EXPOSE 8501

# Define environment variables
# The backend service URL uses the K8s service name created in backend/k8s-service.yaml
ENV BACKEND_API_URL="http://ai-govbot-backend-service:8000/answer_query/"
# Ensure streamlit.py uses this env var, or hardcode carefully:
# ENV STREAMLIT_SERVER_PORT=8501 # Already set in CMD below

# Run streamlit.py when the container launches
# Assumes streamlit.py is runnable via src.frontend.streamlit
CMD ["streamlit", "run", "src/frontend/streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"]