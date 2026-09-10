import json                              # ← FIXED: was importing json from flask
import os
from flask import Flask, render_template, request, session, redirect
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

mysql = MySQL()
app = Flask(__name__)

app.config['MYSQL_USER']     = os.environ.get('MYSQL_USER', 'flaskuser')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', 'flaskpassword')
app.config['MYSQL_DB']       = os.environ.get('MYSQL_DB', 'flaskdb')
app.config['MYSQL_HOST']     = os.environ.get('MYSQL_HOST', 'db')
mysql.init_app(app)

app.secret_key = 'why would I tell you my secret key?'

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
    cursor = None
    try:
        _username = request.form['inputEmail']
        _password = request.form['inputPassword']
        con = mysql.connection
        cursor = con.cursor()
        cursor.callproc('sp_validateLogin', (_username,))
        data = cursor.fetchall()
        if len(data) > 0:
            stored_hash = data[0][3]
            if isinstance(stored_hash, bytes):
                stored_hash = stored_hash.decode('utf-8')
            if check_password_hash(stored_hash, _password):
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


@app.route('/api/signup', methods=['POST'])
def signUp():
    cursor = None
    try:
        _name = request.form['inputName']
        _email = request.form['inputEmail']
        _password = request.form['inputPassword']

        if _name and _email and _password:
            conn = mysql.connection
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
    app.run(host='0.0.0.0', port=5000)     # ← FIXED: must bind 0.0.0.0 inside container