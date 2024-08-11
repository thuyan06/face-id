import os
import re
import io
import zlib
from werkzeug.utils import secure_filename
from flask import Response
from cs50 import SQL
from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory, flash, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import face_recognition
from PIL import Image
from base64 import b64encode, b64decode
import re
from face_recognition import face_distance
from playsound import playsound

# cd C:\Users\rehbe\Downloads\facelogin-main 
# python face_demo.py C:\Users\rehbe\Downloads\face_demo.jpg

from helpers import apology, login_required
# Configure application
app = Flask(__name__)
#configure flask-socketio

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
@app.route("/add_task", methods=["POST"])
@login_required
def add_task():
    data = request.get_json()
    title = data.get("title")
    description = data.get("description")
    due_date = data.get("due_date")
    color = data.get("color", "#3788d8")  # Defaultfarbe, wenn keine angegeben wird

    if not title:
        return jsonify({"error": "Title is required"}), 400
    if not description or not due_date:
        return jsonify({"error": "Missing data"}), 400
    
    db.execute("INSERT INTO tasks (user_id, title, description, due_date, color) VALUES (:user_id, :title, :description, :due_date, :color)",
               user_id=session["user_id"], title=title, description=description, due_date=due_date, color=color)
    return jsonify({"message": "Task added successfully"}), 201

@app.route("/update_task_date/<int:task_id>", methods=["PUT"])
@login_required
def update_task_date(task_id):
    data = request.get_json()
    due_date = data.get('due_date')

    if not due_date:
        return jsonify({"error": "Missing required field: due_date"}), 400

    # Konvertierung von ISO 8601 String zu Datum
    # Hier solltest du eventuell Datumskonvertierung und Fehlerbehandlung hinzufügen

    result = db.execute("UPDATE tasks SET due_date = :due_date WHERE id = :task_id AND user_id = :user_id",
                        due_date=due_date, task_id=task_id, user_id=session["user_id"])

    if result:
        return jsonify({"message": "Task date updated successfully"}), 200
    else:
        return jsonify({"error": "Task update failed"}), 500

@app.route("/update_task/<int:task_id>", methods=["PUT"])
@login_required
def update_task(task_id):
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    due_date = data.get('due_date')
    color = data.get('color')

    if not title or not description or not due_date:
        return jsonify({"error": "Missing required fields"}), 400

    # Konvertierung von ISO 8601 String zu Datum und Anpassung (falls notwendig)


    result = db.execute("UPDATE tasks SET title = :title, description = :description, due_date = :due_date, color = :color WHERE id = :task_id AND user_id = :user_id",
                        title=title, description=description, due_date=due_date, color=color, task_id=task_id, user_id=session["user_id"])

    return jsonify({"message": "Task updated successfully", "task_id": task_id}), 200


@app.route("/delete_task/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task(task_id):
    result = db.execute("DELETE FROM tasks WHERE id = :task_id AND user_id = :user_id",
                        task_id=task_id, user_id=session["user_id"])

    return jsonify({"message": "Task deleted successfully", "task_id": task_id}), 200


@app.route("/tasks")
@login_required
def tasks():
    tasks = db.execute("SELECT id, title, description, due_date, color FROM tasks WHERE user_id = :user_id ORDER BY due_date",
                       user_id=session["user_id"])
    return jsonify(tasks)


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///data.db")

@app.route("/")
@login_required
def home():
    # Entscheidung des Themes basierend auf der Session
    theme_mode = 'darkmode.css' if session.get('darkMode', False) else 'lightmode.css'
    session['theme_mode'] = theme_mode  # Speichern des Themes in der Session
    
    # Weiterleitung zur Hauptseite
    return redirect("/home")

@app.route("/home")
@login_required
def index():
    # Holen des Themes aus der Session
    theme_mode = session.get('theme_mode', 'lightmode.css')
    
    # Abrufen der Benutzerdaten aus der Datenbank
    user = db.execute("SELECT username FROM users WHERE id = :id", id=session["user_id"])
    if user:
        username = user[0]['username']
    else:
        # Fehlerbehandlung, falls kein Benutzer gefunden wird
        flash("User not found. Please log in again.")
        return redirect("/logout")

    # Template rendern mit Benutzername und Theme
    return render_template("index.html", username=username, theme_mode=theme_mode)



@app.route('/toggle-theme', methods=['POST'])
def toggle_theme():
    current_mode = session.get('darkMode', False)
    session['darkMode'] = not current_mode  # Wechselt den Zustand
    return '', 204

@app.context_processor
def inject_theme():
    theme_mode = 'darkmode.css' if session.get('darkMode', False) else 'lightmode.css'
    return dict(theme_mode=theme_mode)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    dark_mode = session.get('darkMode', False)

    # Forget any user_id
    session.clear()

    # Restore dark mode setting
    session['darkMode'] = dark_mode

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Assign inputs to variables
        input_username = request.form.get("username")
        input_password = request.form.get("password")

        # Ensure username was submitted
        if not input_username:
            return render_template("login.html",messager = 1)



        # Ensure password was submitted
        elif not input_password:
             return render_template("login.html",messager = 2)

        # Query database for username
        username = db.execute("SELECT * FROM users WHERE username = :username",
                              username=input_username)

        # Ensure username exists and password is correct
        if len(username) != 1 or not check_password_hash(username[0]["hash"], input_password):
            return render_template("login.html",messager = 3)

        # Remember which user has logged in
        session["user_id"] = username[0]["id"]



        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    dark_mode = session.get('darkMode', False)

    # Forget any user_id
    session.clear()

    # Restore dark mode setting
    session['darkMode'] = dark_mode

    return redirect("/")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Assign inputs to variables
        input_username = request.form.get("username")
        input_password = request.form.get("password")
        input_confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not input_username:
            return render_template("register.html",messager = 1)

        # Ensure password was submitted
        elif not input_password:
            return render_template("register.html",messager = 2)

        # Ensure passwsord confirmation was submitted
        elif not input_confirmation:
            return render_template("register.html",messager = 4)

        elif not input_password == input_confirmation:
            return render_template("register.html",messager = 3)

        # Query database for username
        username = db.execute("SELECT username FROM users WHERE username = :username",
                              username=input_username)

        # Ensure username is not already taken
        if len(username) == 1:
            return render_template("register.html",messager = 5)

        # Query database to insert new user
        else:
            new_user = db.execute("INSERT INTO users (username, hash) VALUES (:username, :password)",
                                  username=input_username,
                                  password=generate_password_hash(input_password, method="pbkdf2:sha256", salt_length=8),)

            if new_user:
                # Keep newly registered user logged in
                session["user_id"] = new_user

            # Flash info for the user
            flash(f"Registered as {input_username}")

            # Redirect user to homepage
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route('/voices/voice2.mp3')
def serve_audio():
    return send_from_directory('voices', 'voice2.mp3')

@app.route('/red')
def red():
    return render_template("register.html")


@app.route("/facereg", methods=["GET", "POST"])
def facereg():
    if request.method == "POST":
        encoded_image = request.form.get("pic").encode('utf-8')
        username = request.form.get("name")
        user_record = db.execute("SELECT * FROM users WHERE username = :username", username=username)

        if len(user_record) != 1:
            flash("User not found.")
            return render_template("camera.html", retry=True, message=1)  # Added message for clarity

        user_id = user_record[0]['id']
        decoded_data = b64decode(encoded_image)
        uploaded_image_path = './static/face/uploaded_' + str(user_id) + '.jpg'
        with open(uploaded_image_path, 'wb') as new_image_handle:
            new_image_handle.write(decoded_data)

        try:
            uploaded_image = face_recognition.load_image_file(uploaded_image_path)
            uploaded_face_encodings = face_recognition.face_encodings(uploaded_image)
            if not uploaded_face_encodings:
                flash("No face detected in the uploaded image. Please try again.")
                return render_template("camera.html", retry=True, message=2)  # No face detected

            reference_image_path = './static/face/' + str(user_id) + '.jpg'
            reference_image = face_recognition.load_image_file(reference_image_path)
            reference_face_encodings = face_recognition.face_encodings(reference_image)
            if not reference_face_encodings:
                flash("No reference face found. Please contact support.")
                return render_template("camera.html", retry=False, message=5)  # Cannot retry, no reference

            face_distances = face_recognition.face_distance([reference_face_encodings[0]], uploaded_face_encodings[0])
            if face_distances[0] <= 0.4:
                session["user_id"] = user_id
                return jsonify(success=True)
            else:
                flash("Face match failed. Please try again.")
                return render_template("camera.html", retry=True, message=3)  # Face match failed
        except Exception as e:
            flash(f"Error processing image: {str(e)}")
            return render_template("camera.html", retry=True, message=4)  # Error processing image

    else:
        return render_template("camera.html", retry=False)


@app.route("/facesetup", methods=["GET", "POST"])
def facesetup():
    if request.method == "POST":


        encoded_image = (request.form.get("pic")+"==").encode('utf-8')


        id_=db.execute("SELECT id FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["id"]
        # id_ = db.execute("SELECT id FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["id"]    
        compressed_data = zlib.compress(encoded_image, 9) 
        
        uncompressed_data = zlib.decompress(compressed_data)
        decoded_data = b64decode(uncompressed_data)
        
        new_image_handle = open('./static/face/'+str(id_)+'.jpg', 'wb')
        
        new_image_handle.write(decoded_data)
        new_image_handle.close()
        image_of_bill = face_recognition.load_image_file(
        './static/face/'+str(id_)+'.jpg')    
        try:
            bill_face_encoding = face_recognition.face_encodings(image_of_bill)[0]
        except:    
            return render_template("face.html",message = 1)
        return redirect("/home")

    else:
        return render_template("face.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("error.html",e = e)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == '__main__':
      app.run()
