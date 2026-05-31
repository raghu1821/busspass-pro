import sys
sys.path.append('c:/Users/ragha/OneDrive/Documents/PROJECT/BUSS_PASS_MANAGEMENT')
from app import app, get_db

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user'] = 'test_user'
        
    db = get_db()
    c = db.cursor()
    c.execute("INSERT INTO Pass_Application (passenger_name, status, duration_months) VALUES ('test_user', 'Approved', 1)")
    db.commit()
    c.execute("SELECT LAST_INSERT_ID()")
    app_id = c.fetchone()[0]
    
    resp = client.post(f'/activate_pass/{app_id}')
    print('STATUS:', resp.status_code)
    print('DATA:', resp.data)
