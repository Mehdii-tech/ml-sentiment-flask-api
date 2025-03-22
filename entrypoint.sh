#!/bin/bash
set -e

# Export environment variables so cron can source them
env | grep -v "PATH\|HOME\|TERM" > /etc/environment

echo "Waiting for MySQL to be ready..."

# Function to test MySQL connection
test_mysql() {
    python3 - << 'EOF'
import pymysql
import time
import os
from urllib.parse import urlparse

def check_db():
    try:
        db_url = os.getenv("DATABASE_URL", "")
        if db_url:
            parsed = urlparse(db_url)
            host = parsed.hostname or "db"
            user = parsed.username or "user"
            password = parsed.password or "password"
            database = parsed.path.lstrip("/") or "tweet_sentiment"
        else:
            host = "db"
            user = "user"
            password = "password"
            database = "tweet_sentiment"
            
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM tweets")
            count = cursor.fetchone()[0]
            return count > 0
    except Exception as e:
        return False

# Try to connect for 2 minutes (24 attempts * 5 seconds)
for i in range(24):
    if check_db():
        print("Database is ready and contains seed data!")
        exit(0)
    time.sleep(5)

print("Could not verify database readiness")
exit(1)
EOF
}

while ! test_mysql; do
    echo "Waiting for MySQL to be fully initialized..."
    sleep 5
done

echo "MySQL is ready!"

# Create (or ensure) the cron log file exists
touch /var/log/cron.log

# Start cron daemon in the background
cron

# Log a startup message (this will appear in /var/log/cron.log)
echo "ML container started. Cron job scheduled and Flask app starting..." >> /var/log/cron.log

# Start your Flask app in the background (its output goes to the same log)
python app.py >> /var/log/cron.log 2>&1 &

# Tail the log file to keep the container alive
tail -f /var/log/cron.log
