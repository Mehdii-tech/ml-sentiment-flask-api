FROM python:3.9-slim

WORKDIR /app

# Install only netcat for database connection checking
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create wait-for-it script
RUN echo '#!/bin/bash\n\
while ! nc -z db 3306; do\n\
  echo "Waiting for MySQL..."\n\
  sleep 1\n\
done\n\
echo "MySQL is ready!"\n\
python app.py' > /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["/app/entrypoint.sh"] 