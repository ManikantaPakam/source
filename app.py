import os
from flask import Flask, flash, request, redirect, jsonify, session, url_for, render_template
from flask_mysqldb import MySQL
import logging
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb.cursors
import logging
import base64
import os
from flask_login import UserMixin,login_required, current_user, LoginManager, login_user, logout_user


logging.basicConfig(level=logging.DEBUG)


UPLOAD_FOLDER = 'Home/Manikanta/VISTAN PROJECT/web-speech-recorder/web-speech-recorder/source/static/audios'
BASE_DIR = '/home/vistan-desktop-10/Manikanta/VISTAN PROJECTS/web-speech-recorder/web-speech-recorder/source/static/users_photos'

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = 'your secret key'
 
 
app.config['MYSQL_HOST'] = '10.147.17.141'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin123'
app.config['MYSQL_DB'] = 'Language_Translation'

 
mysql = MySQL(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE personID = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
        return User(id=user['personID'], username=user['username'], email=user['email'], photo=user['photo'])
    return None

class User(UserMixin):
    def __init__(self, id, username, email, photo):
        self.id = id
        self.username = username
        self.email = email
        self.photo = photo
        
    @staticmethod
    def create_user(mysql, username, email, address, mobile, photo, password):
        cursor = mysql.connection.cursor()
        hashed_password = generate_password_hash(password)
        try:
            cursor.execute('INSERT INTO users (username, email, address, mobile, photo, password) VALUES (%s, %s, %s, %s, %s, %s)', 
                           (username, email, address, mobile, photo, hashed_password))
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
            logging.debug(f"User {user['username']} logged in successfully.")
            return User(id=user['personID'], username=user['username'], email=user['email'], photo=user['photo'])
        logging.debug("Failed to login user.")
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


    @staticmethod
    def get_language_data(mysql, username):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT inputlanguage, outputlanguage FROM selectlanguage WHERE username_FK = %s ORDER BY field_id DESC LIMIT 1', (username,))
        data = cursor.fetchone()
        cursor.close()
        return data


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

#-------------------------Login views------------------------------
            
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.login_user(mysql, email, password)
        if user:
            login_user(user)
            logging.debug(f"Logged in user: {user.username}")
            flash('Login successful!', 'success')
            return redirect(url_for('root'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        address = request.form['address']
        mobile = request.form['mobile']
        photo = request.files['profile']
        password = request.form['password']

        if photo:
            photo_path = os.path.join(BASE_DIR, photo.filename)
            photo.save(photo_path) 
            photo_filename = photo.filename
        else:
            flash('No photo uploaded', 'danger')
            return redirect(url_for('register'))

        if User.create_user(mysql, username, email, address, mobile, photo_filename, password):
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Please try again.', 'danger')
    return render_template('register.html')

#-----------------------------End-------------------------------------

#-----------------------------LOGOUT VIEW-----------------------------

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

#------------------------------End-----------------------------------

@app.route('/language')
@login_required
def root():
    return render_template('language.html', user=current_user)


@app.route('/recorder', methods=['GET', 'POST'])
@login_required
def recorder():
    if request.method == 'POST':
        username = current_user.username
        language_data = selectlanguage.get_language_data(mysql, username)

        if language_data:
            inputlanguage = language_data['inputlanguage']
            outputlanguage = language_data['outputlanguage']
            selectedprofile = request.form.get('job')
            if selectprofile.select_profile(mysql, username, inputlanguage, outputlanguage, selectedprofile):
                flash('Profile selection saved successfully.', 'success')
            else:
                flash('Failed to save profile selection.', 'danger')
        return redirect(url_for("recorder"))
    return render_template('index.html', user=current_user)


@app.route('/submit', methods=['POST'])
@login_required
def submit():
    if not current_user.is_authenticated:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))
    username = current_user.username
    if request.method == 'POST':
        input_lang = request.form['input']
        output_lang = request.form['output']
        if selectlanguage.select_language(mysql, username, input_lang, output_lang):
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for("recorder"))
        else:
            flash('Registration failed. Please try again.', 'danger')


@app.route('/save-record', methods=['POST'])
@login_required
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

#-----------------------------API'S--------------------------------------

@app.route('/api/latest_language', methods=['GET'])
def get_latest_language():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        'SELECT inputlanguage, outputlanguage FROM selectlanguage ORDER BY field_id DESC LIMIT 1'
    )
    latest_language = cursor.fetchone()
    cursor.close()
    
    if latest_language:
        return jsonify(latest_language), 200
    else:
        return jsonify({'message': 'No data found'}), 404


@app.route('/api/latest_profile', methods=['GET'])
@login_required
def get_latest_profile():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        'SELECT inputlanguage, outputlanguage, selectedprofile FROM selectprofile ORDER BY field_id DESC LIMIT 1'
        )
    latest_profile = cursor.fetchone()
    cursor.close()

    if latest_profile:
        return jsonify(latest_profile), 200
    else:
        return jsonify({'message': 'No data found'}), 404

#-----------------------------END--------------------------------------

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=8005) 
