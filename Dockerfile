FROM python:3.9-slim

WORKDIR /app

# Install cron and netcat (for database connection checking)
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Copy your crontab file into the proper location
COPY crontab /etc/cron.d/model-retraining
RUN chmod 0644 /etc/cron.d/model-retraining
RUN crontab /etc/cron.d/model-retraining

# Copy your updated entrypoint.sh into the container and make it executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose the port your app runs on
EXPOSE 5000

# Use your entrypoint script as the container's entrypoint
ENTRYPOINT ["/entrypoint.sh"]
