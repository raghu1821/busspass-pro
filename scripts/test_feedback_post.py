from app import app, get_db
import sys

with app.test_request_context('/feedback', method='POST', data={'message': 'This is a test feedback message that is over 20 characters', 'topic': 'General'}):
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user'] = 'testuser'
            sess['admin'] = 'testadmin'
        try:
            response = client.post('/feedback', data={'message': 'This is a test feedback message that is over 20 characters', 'topic': 'General'})
            print(f"Status: {response.status_code}")
            if response.status_code == 500:
                print(response.data.decode('utf-8'))
        except Exception as e:
            import traceback
            traceback.print_exc()
