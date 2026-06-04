from app import app, get_db
import sys

with app.test_request_context('/feedback', method='GET'):
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user'] = 'testuser'
            sess['admin'] = 'testadmin'
        try:
            response = client.get('/feedback')
            print(f"User Feedback Status: {response.status_code}")
            if response.status_code == 500:
                print(response.data.decode('utf-8'))
                
            response = client.get('/view_feedback')
            print(f"Admin Feedback Status: {response.status_code}")
            if response.status_code == 500:
                print(response.data.decode('utf-8'))
        except Exception as e:
            import traceback
            traceback.print_exc()
