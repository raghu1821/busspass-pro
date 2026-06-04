from flask import Flask, render_template, session
app = Flask(__name__, template_folder='templates')
app.secret_key='test'

@app.route('/')
def test():
    session['user'] = 'testuser'
    return render_template('dashboard.html', user='testuser', applications=[])

if __name__ == '__main__':
    with app.test_client() as c:
        try:
            res = c.get('/')
            print(res.status_code)
        except Exception as e:
            print("ERROR:", e)
