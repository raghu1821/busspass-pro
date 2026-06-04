from app import get_db
db = get_db()
c = db.cursor()
try:
    c.execute("ALTER TABLE Feedback ADD COLUMN topic VARCHAR(50) DEFAULT 'General'")
    db.commit()
    print("SUCCESS: Added topic column to Feedback table")
except Exception as e:
    print(f"Note: {e}")

# Verify schema
c.execute("DESCRIBE Feedback")
for col in c.fetchall():
    print(col)
