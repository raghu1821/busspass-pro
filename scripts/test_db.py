import sys
sys.path.append('c:/Users/ragha/OneDrive/Documents/PROJECT/BUSS_PASS_MANAGEMENT')
from app import get_db
db = get_db()
c = db.cursor()
c.execute("DESCRIBE Passenger")
for row in c.fetchall(): print(row)
