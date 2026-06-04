import sys
sys.path.append('c:/Users/ragha/OneDrive/Documents/PROJECT/BUSS_PASS_MANAGEMENT')
from app import get_db
db = get_db()
c = db.cursor()
c.execute("DELETE FROM Pass")
db.commit()
print('Cleared all old passes')
