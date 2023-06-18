import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

load_dotenv()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50))
    username = db.Column(db.String(50), default="")
    username_unfinished = db.Column(db.String(50), default="")
    unicode_string = db.Column(db.String(50), default="")
    color = db.Column(db.String(50), default="ffffff")
    color_red = db.Column(db.Integer, default=255)
    color_green = db.Column(db.Integer, default=255)
    color_blue = db.Column(db.Integer, default=255)

    registration_time = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, ip_address):
        self.ip_address = ip_address

def create_account():
    ip_address = get_ip()
    user = User(ip_address)
    db.session.add(user)
    db.session.commit()

def reset_account(user):
    db.session.delete(user)
    db.session.commit()
    create_account()

def get_ip():
    ip_addresses = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')
    ip_address = ip_addresses[0].strip()
    return ip_address

def get_user():
    ip_address = get_ip()
    user = User.query.filter_by(ip_address=ip_address).first()
    return user

def get_username_list():
    users = User.query.filter(User.username != "").order_by(User.registration_time.desc()).all()
    username_list = ",".join(user.username for user in users)
    return username_list

def letter_to_name(user, letter):
    user.username_unfinished += letter
    db.session.commit()


def get_info_as_json():
    users = User.query.filter(User.username != "").order_by(User.registration_time.desc()).all()
    usernames = ",".join(user.username for user in users)
    ids = ",".join(str(user.id) for user in users)
    colors = ",".join(str(user.color) for user in users)


    data = {
        "usernames": usernames,
        "ids": ids,
        "colors": colors,
    }

    return jsonify(data)

def unicode_to_name(user):
    unicode_string = user.unicode_string
    if(len(unicode_string) > 3):
        try:
            unicode_value = int(unicode_string, 16)
            unicode_char = str(chr(unicode_value))
            print(unicode_char)
            user.username_unfinished += unicode_char
            user.unicode_string = ""
            db.session.commit()
        except:
            print("ERROR")
            pass

def update_color_hex(user):
    # Ensure that the RGB values are within the valid range of 0-255
    r = max(0, min(255, user.color_red))
    g = max(0, min(255, user.color_green))
    b = max(0, min(255, user.color_blue))

    # Convert the RGB values to hexadecimal format
    hex_code = "#{:02x}{:02x}{:02x}".format(r, g, b)
    user.color = hex_code

    db.session.commit()

def update_last_seen(user):
    user.last_seen = datetime.utcnow
    db.session.commit()

@app.route("/color/red/<value>")
def color_red(value):
    user = get_user()
    if(user is None): return "Not registered"
    user.color_red = int(value)
    db.session.commit()
    return "Red updated"

@app.route("/color/green/<value>")
def color_green(value):
    user = get_user()
    if(user is None): return "Not registered"
    user.color_green = int(value)
    db.session.commit()
    return "Green updated"

@app.route("/color/blue/<value>")
def color_blue(value):
    user = get_user()
    if(user is None): return "Not registered"
    user.color_blue = int(value)
    db.session.commit()
    update_color_hex(user)
    return "Color updated"

@app.route("/get_data")
def get_data():
    user = get_user()
    if(user is not None):
        update_last_seen(user)
    return get_info_as_json()

@app.route("/login_as/<number>")
def login_as(number):
    ip_address = get_ip()
    user = User.query.filter(User.id == int(number)).first()
    if(user is None): return "Not registered"
    user.ip_address = ip_address
    db.session.commit()
    update_last_seen(user)
    return "Logged in as: " + user.username

@app.route("/login")
def login():
    user = get_user()
    if user is None:
        create_account()
    elif user.username == "":
        reset_account(user)
    else:
        update_last_seen(user)
        #login


    return get_info_as_json()


@app.route("/unicode/start/<letter>")
def start(letter):
    user = get_user()
    if(user is None): return "Not registered"
    unicode_to_name(user)
    user.unicode_string = letter
    db.session.commit()

    return "Current username: " + user.username_unfinished


@app.route("/unicode/continue/<letter>")
def continue_string(letter):
    user = get_user()
    if(user is None): return "Not registered"

    user.unicode_string += letter
    db.session.commit()

    return "Current string: " + user.unicode_string

@app.route("/letter/<letter>")
def add_letter(letter):
    user = get_user()
    if(user is None): return "Not registered"
    unicode_to_name(user)
    letter_to_name(user, letter)
    return "Current string: " + user.unicode_string


@app.route("/finish_username")
def finish_username():
    user = get_user()
    if(user is None): return "Not registered"
    unicode_to_name(user)
    user.username = user.username_unfinished
    user.username_unfinished = ""
    db.session.commit()
    update_last_seen(user)

    return "Account created: " + user.username


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()