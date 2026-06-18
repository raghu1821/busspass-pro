import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import get_db
db = get_db()
c = db.cursor()
c.execute("DELETE FROM Pass")
db.commit()
print('Cleared all old passes')
