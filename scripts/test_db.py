import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import get_db
db = get_db()
c = db.cursor()
c.execute("DESCRIBE Passenger")
for row in c.fetchall(): print(row)
