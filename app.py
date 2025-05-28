# app.py
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- Database Configuration ---
# Use an absolute path for the SQLite database file
# This is crucial for Render, as it expects a fixed location
# 'site.db' will be created in the root of your backend project
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Suppress a warning

db = SQLAlchemy(app)

# --- CORS Configuration ---
CORS(app) # Enable CORS for all routes

# --- Database Model ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    # New 'role' column, default to 0
    # You can define what 0 and 1 mean (e.g., 0=standard user, 1=admin/special access)
    role = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<User {self.email} - Role: {self.role}>"

    # Method to convert User object to dictionary (useful for JSON response)
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role
        }

# --- Create Database Tables (Run this once or on app startup) ---
# This block ensures tables are created when the app context is pushed.
# On Render, this will run on each deployment, creating the file if it doesn't exist.
with app.app_context():
    db.create_all()

# --- Routes ---

@app.route('/')
def home():
    """A simple home route to check if the backend is running."""
    return "Internboat Backend is running! (API endpoints: /register, /view-registrations, /login, /courses)"

@app.route('/register', methods=['POST'])
def register():
    """Handles new user registrations and saves to DB."""
    if not request.is_json:
        return jsonify({"message": "Request must be JSON"}), 400

    data = request.get_json()
    name = data.get('name')
    email = data.get('email')

    if not name or not email:
        return jsonify({"message": "Name and email are required"}), 400

    # Check if email already exists in the database
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"message": "Email already registered"}), 409 # 409 Conflict

    # Create a new User object and add to database
    # Role defaults to 0 as defined in the model
    new_user = User(name=name, email=email)
    db.session.add(new_user)
    db.session.commit()

    print(f"Registered new user: Name='{name}', Email='{email}', Role='{new_user.role}'")
    return jsonify({"message": "Registration successful!", "user": new_user.to_dict()}), 201

@app.route('/view-registrations', methods=['GET'])
def view_registrations():
    """Returns all registered users from the database."""
    users = User.query.all()
    # Convert list of User objects to list of dictionaries for JSON serialization
    return jsonify([user.to_dict() for user in users])

@app.route('/login', methods=['POST'])
def login():
    """Handles user login verification and returns user role."""
    if not request.is_json:
        return jsonify({"message": "Request must be JSON"}), 400

    data = request.get_json()
    entered_name = data.get('name')
    entered_email = data.get('email')

    if not entered_name or not entered_email:
        return jsonify({"message": "Name and email are required"}), 400

    # Query the database for a user with matching name and email
    user = User.query.filter_by(name=entered_name, email=entered_email).first()

    if user:
        # Login successful! Return user's role.
        return jsonify({
            "message": "Login successful!",
            "status": "success",
            "user": {
                "name": user.name,
                "email": user.email,
                "role": user.role # IMPORTANT: Return the user's role
            }
        }), 200
    else:
        return jsonify({"message": "Invalid name or email", "status": "fail"}), 401

@app.route('/courses', methods=['GET'])
def get_courses():
    """Provides a list of courses with prices for Role 0 users."""
    courses = [
        {"id": "python-basics", "name": "Python Basics", "price": 499, "image": "python_course.jpg"},
        {"id": "web-dev-101", "name": "Web Development 101", "price": 799, "image": "web_dev_course.jpg"},
        {"id": "cpp-fundamentals", "name": "C++ Fundamentals", "price": 599, "image": "cpp_course.jpg"},
        {"id": "data-science-intro", "name": "Introduction to Data Science", "price": 999, "image": "data_science_course.jpg"}
    ]
    return jsonify(courses)


# This part is for local development only
if __name__ == '__main__':
    # Initialize the database within the application context when running locally
    # This creates site.db if it doesn't exist
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)