import os
from flask import Flask, flash, request, redirect, jsonify, url_for
from flask_mysqldb import MySQL
import logging
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb.cursors
import logging
from flask_login import UserMixin,login_required, current_user, LoginManager


logging.basicConfig(level=logging.DEBUG)

form_data = []

UPLOAD_FOLDER = '/home/vistan/Desktop/Robo-Teacher/web-speech-recorder/source/static/audios'

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = 'your secret key'
 
 
app.config['MYSQL_HOST'] = '10.147.17.141'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin123'
app.config['MYSQL_DB'] = 'LanguageTranslation'

 
mysql = MySQL(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id) 


class User(UserMixin):
    @staticmethod
    def create_user(mysql, username, email, address, mobile, photo, password):
        cursor = mysql.connection.cursor()
        hashed_password = generate_password_hash(password)
        try:
            cursor.execute('INSERT INTO users (username, email, address, mobile, photo, password) VALUES (%s, %s, %s, %s, %s, %s)', (username, email, address, mobile, photo, hashed_password))
            mysql.connection.commit()
            return True
        except Exception as e:
            logging.error(f"Error: {e}")
            return False
        finally:
            cursor.close()
    
    @staticmethod
    def login_user(mysql, email, password):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        cursor.close()
        if user and check_password_hash(user['password'], password):
            return user
        return None

    @staticmethod
    def get(user_id):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            return User(**user)
        return None

    def get_id(self):
        return str(self.id)

    @staticmethod
    def login_user(mysql, email, password):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        cursor.close()
        if user and check_password_hash(user['password'], password):
            return user
        return None


class selectlanguage:
    @staticmethod
    def select_language(mysql, username_FK, inputlanguage, outputlanguage):
        cursor = mysql.connection.cursor()
        try:
            cursor.execute('INSERT INTO selectlanguage (username_FK, inputlanguage, outputlanguage) VALUES (%s, %s, %s)', (username_FK, inputlanguage, outputlanguage))
            mysql.connection.commit()
            return True
        except Exception as e:
            logging.error(f"Error:{e}")
            return False
        finally:
            cursor.close()


class selectprofile:
    @staticmethod
    def select_profile(mysql, username, inputlanguage, outputlanguage, selectedprofile):
        cursor = mysql.connection.cursor()
        try:
            cursor.execute('INSERT INTO selectprofile (username, inputlanguage, outputlanguage, selectedprofile) VALUES (%s, %s, %s, %s)', (username, inputlanguage, outputlanguage, selectedprofile))
            mysql.connection.commit()
            return True
        except Exception as e:
            logging.error(f"Error:{e}")
            return False
        finally:
            cursor.close()


@app.route('/language')
def root():
    return app.send_static_file('language.html')


@app.route('/recorder')
def recorder():
    return app.send_static_file('index.html')


@app.route('/submit', methods=['POST'])
@login_required
def submit():
    username = current_user.user
    print('Username_Print',username)
    if request.method == 'POST':
        input_lang = request.form['input']
        output_lang = request.form['output']
        if selectlanguage.select_language(mysql, username, input_lang, output_lang):
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for("recorder"))
        else:
            flash('Registration failed. Please try again.', 'danger')
    # form_data.append({'input': input_lang, 'output': output_lang})
    # return redirect(url_for("recorder"))


@app.route('/save-record', methods=['POST'])
def save_record():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    file_name = "audio.mp3"
    full_file_name = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    file.save(full_file_name)
    return '<h1>Success</h1>'

#-------------------------Login views------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        address = request.form['address']
        mobile = request.form['mobile']
        photo = request.form['profile']
        password = request.form['password']
        if User.create_user(mysql, username, email, address, mobile, photo, password):
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Please try again.', 'danger')
    return app.send_static_file('register.html')


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.login_user(mysql, email, password)
        if user:
            flash('Login successful!', 'success')
            return redirect(url_for('root'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return app.send_static_file('login.html')



#-----------------------------End-------------------------------------


#-----------------------------API--------------------------------------

@app.route('/api/form_data', methods=['GET'])
def get_form_data():
    latest_submission = form_data[-1] if form_data else {}
    return jsonify(latest_submission)


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=8004) 
