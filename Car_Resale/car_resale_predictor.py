from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import pickle
import numpy as np

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database Setup - Use PostgreSQL for deployment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///users.db")  # Uses SQLite locally
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Initialize Database
with app.app_context():
    db.create_all()

# Load Model & Encoders
try:
    model = pickle.load(open("Car_Resale/model.pkl", "rb"))
    brand_encoder = pickle.load(open("Car_Resale/brand.pkl", "rb"))
    fuel_type_encoder = pickle.load(open("Car_Resale/fuel_type.pkl", "rb"))
    transmission_encoder = pickle.load(open("Car_Resale/transmission.pkl", "rb"))
except Exception as e:
    print(f"Error loading model or encoders: {e}")
    model, brand_encoder, fuel_type_encoder, transmission_encoder = None, None, None, None

# Home Route
@app.route('/')
def home():
    return render_template('index.html')

# Signup Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if email and password:
            hashed_password = generate_password_hash(password)  # Secure password storage
            new_user = User(email=email, password=hashed_password)
            try:
                db.session.add(new_user)
                db.session.commit()
                flash("Signup successful! Please log in.", "success")
                return redirect(url_for('login'))
            except:
                flash("Email already exists. Try logging in.", "danger")
        else:
            flash("All fields are required.", "danger")

    return render_template('signup.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user'] = email
            flash("Login successful!", "success")
            return redirect(url_for('predict'))
        else:
            flash("Invalid credentials. Try again.", "danger")

    return render_template('login.html')

# Predict Route
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            car_age = int(request.form['car_age'])
            mileage = float(request.form['mileage'])
            brand = request.form['brand']
            fuel_type = request.form['fuel_type']
            transmission = request.form['transmission']

            # Validate categorical values
            if brand not in brand_encoder.classes_:
                flash("Error: Unknown brand.", "danger")
                return redirect(url_for('predict'))
            if fuel_type not in fuel_type_encoder.classes_:
                flash("Error: Unknown fuel type.", "danger")
                return redirect(url_for('predict'))
            if transmission not in transmission_encoder.classes_:
                flash("Error: Unknown transmission type.", "danger")
                return redirect(url_for('predict'))

            # Encode categorical values
            brand_encoded = brand_encoder.transform([brand])[0]
            fuel_type_encoded = fuel_type_encoder.transform([fuel_type])[0]
            transmission_encoded = transmission_encoder.transform([transmission])[0]

            # Prepare input features
            input_features = np.array([[car_age, mileage, brand_encoded, fuel_type_encoded, transmission_encoded]])

            # Predict price
            predicted_price = model.predict(input_features)[0]

            return render_template('predict.html', prediction=f"Estimated price: ₹{predicted_price:.2f}")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    return render_template('predict.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully!", "info")
    return redirect(url_for('home'))

# Run Flask App
if __name__ == '__main__':
    app.run(debug=True)



