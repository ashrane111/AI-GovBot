FROM apache/airflow:2.10.5-python3.10

# Install required dependencies for compiling packages
USER root
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    python3-dev \
    libprotobuf-dev \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Copy requirements and install dependencies
ADD requirements.txt .
# RUN pip install apache-airflow==${AIRFLOW_VERSION} -r requirements.txt
RUN pip install -r requirements.txt


# Install Google Cloud SDK
RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH $PATH:/root/google-cloud-sdk/bin
