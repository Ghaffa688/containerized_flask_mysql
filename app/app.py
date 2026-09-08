import os
from flask import Flask, render_template, json, request, session, redirect
from flaskext.mysql import MySQL
from werkzeug.security import generate_password_hash, check_password_hash


def read_secret(env_name, default=None):
    """Read a value from ENV, or from a file if ENV_FILE is set (Docker secrets)."""
    file_path = os.getenv(f"{env_name}_FILE")
    if file_path and os.path.isfile(file_path):
        with open(file_path) as f:
            return f.read().strip()
    return os.getenv(env_name, default)


mysql = MySQL()
app = Flask(__name__)

app.config['MYSQL_DATABASE_HOST'] = os.getenv('DB_HOST', 'database')
app.config['MYSQL_DATABASE_USER'] = os.getenv('DB_USER', 'flask_user')
app.config['MYSQL_DATABASE_PASSWORD'] = os.getenv('DB_PASSWORD', 'devpassword')
app.config['MYSQL_DATABASE_DB'] = os.getenv('DB_NAME', 'BucketList')

mysql.init_app(app)

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-only-change-me')

app.secret_key = read_secret('FLASK_SECRET_KEY', 'dev-only-change-me')


@app.route('/')
def main():
    return render_template('index.html')


@app.route('/signup')
def showSignUp():
    return render_template('signup.html')


@app.route('/signin')
def showSignin():
    return render_template('signin.html')


@app.route('/api/validateLogin', methods=['POST'])
def validateLogin():
    conn = None
    cursor = None
    try:
        _username = request.form['inputEmail']
        _password = request.form['inputPassword']

        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.callproc('sp_validateLogin', (_username,))
        data = cursor.fetchall()

        if len(data) > 0:
            if check_password_hash(str(data[0][3]), _password):
                session['user'] = data[0][0]
                return redirect('/userhome')
            else:
                return render_template('error.html', error='Wrong Email address or Password')
        else:
            return render_template('error.html', error='Wrong Email address or Password')
    except Exception as e:
        return render_template('error.html', error=str(e))
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


@app.route('/api/signup', methods=['POST'])
def signUp():
    conn = None
    cursor = None
    try:
        _name = request.form['inputName']
        _email = request.form['inputEmail']
        _password = request.form['inputPassword']

        if _name and _email and _password:
            conn = mysql.connect()
            cursor = conn.cursor()
            _hashed_password = generate_password_hash(_password)
            cursor.callproc('sp_createUser', (_name, _email, _hashed_password))
            data = cursor.fetchall()

            if len(data) == 0:
                conn.commit()
                return json.dumps({'message': 'User created successfully !'})
            else:
                return json.dumps({'error': str(data[0])})
        else:
            return json.dumps({'html': '<span>Enter the required fields</span>'})
    except Exception as e:
        return json.dumps({'error': str(e)})
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


@app.route('/userhome')
def userHome():
    if session.get('user'):
        return render_template('userhome.html')
    else:
        return render_template('error.html', error='Unauthorized Access')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')


if __name__ == "__main__":
    app.run(host="0.0.0.0")