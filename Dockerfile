FROM python:3.9-slim

WORKDIR /app

# Install cron and netcat (for database connection checking)
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    cron \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy and prepare the entrypoint script first to ensure it exists
COPY entrypoint.sh /entrypoint.sh
RUN dos2unix /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Copy your crontab file and ensure it has Unix line endings
COPY crontab /etc/cron.d/model-retraining
RUN dos2unix /etc/cron.d/model-retraining && \
    chmod 0644 /etc/cron.d/model-retraining && \
    crontab /etc/cron.d/model-retraining

# Create directory for models if it doesn't exist
RUN mkdir -p /app/models && chmod 777 /app/models

# Copy the rest of your application code
COPY . .

# Make sure scheduler.py has execute permissions
RUN chmod +x scheduler.py

# Expose the port your app runs on
EXPOSE 5000

# Use your entrypoint script as the container's entrypoint
ENTRYPOINT ["/entrypoint.sh"]