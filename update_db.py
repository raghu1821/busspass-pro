import os
import mysql.connector
import random
from datetime import datetime, timedelta

db_config = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "admin123"),
    "database": os.getenv("DB_NAME", "buspassdb"),
    "port":     int(os.getenv("DB_PORT", 3306))
}

def run():
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    
    # Check if created_at exists
    cursor.execute("SHOW COLUMNS FROM Pass_Application LIKE 'created_at'")
    if not cursor.fetchone():
        print("Adding created_at column...")
        cursor.execute("ALTER TABLE Pass_Application ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        # Backdate existing applications
        cursor.execute("SELECT application_id FROM Pass_Application")
        apps = cursor.fetchall()
        for app in apps:
            app_id = app[0]
            # Random date within last 6 months
            days_ago = random.randint(1, 180)
            random_date = datetime.now() - timedelta(days=days_ago)
            cursor.execute("UPDATE Pass_Application SET created_at = %s WHERE application_id = %s", (random_date, app_id))
        
        db.commit()
        print(f"Backdated {len(apps)} existing applications.")
    else:
        print("created_at column already exists.")

    db.close()

if __name__ == "__main__":
    run()
