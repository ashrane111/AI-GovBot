# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the main requirements file from the src directory (relative to build context)
COPY src/requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the frontend source code (relative to build context)
COPY src/frontend /app/src/frontend

# Make port 8501 available (default Streamlit port)
EXPOSE 8501

# Run streamlit.py when the container launches
CMD ["streamlit", "run", "src/frontend/streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"]