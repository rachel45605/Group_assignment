from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai
import os
from datetime import datetime
import os
import logging
import sys

# Configure logging to show in console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Configure the AI model
# api = os.getenv("MAKERSUITE_API_KEY")
# genai.configure(api_key='AIzaSyDtgxpFE0405T7m7l4llYVzW-eCb_Z-XMg')
# model = genai.GenerativeModel("gemini-1.5-flash")

@app.route('/set_api_key', methods=['POST'])
def set_api_key():
    api_key = request.form['api_key']
    session['api_key'] = api_key  # Store API key in session
    os.environ['API_KEY'] = api_key  # Set the environment variable dynamically
    genai.configure(api_key=api_key)  # Configure Gemini API with the new key
    return redirect(url_for('index'))

db = SQLAlchemy(app)

with app.app_context():
    db.create_all()

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    financial_profiles = db.relationship('FinancialProfile', backref='user', lazy=True)

class FinancialProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    annual_income = db.Column(db.Float)
    risk_level = db.Column(db.String(20))
    investment_horizon = db.Column(db.String(20))
    region = db.Column(db.String(50))
    total_assets = db.Column(db.Float)
    selected_portfolios = db.Column(db.String(500))  # Store as comma-separated string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('homepage.html')

# # Hardcoded API key for testing
# HARD_CODED_API_KEY = "AIzaSyDtgxpFE0405T7m7l4llYVzW-eCb_Z-XMg"

@app.route("/financial_planning", methods=["GET", "POST"])
def financial_planning():
    if request.method == "POST":
        # Debug Step 1: Print raw form data
        print("\n==== Raw Form Data ====")
        print("Form Data:", request.form)
        
        try:
            # Debug Step 2: Extract form data with explicit error checking
            print("\n==== Extracting Form Data ====")
            
            # Get form data with validation
            age = request.form.get("age")
            gender = request.form.get("gender")
            annual_income = request.form.get("annual_income")
            total_assets = request.form.get("total_assets")
            
            print(f"Age: {age}, type: {type(age)}")
            print(f"Gender: {gender}, type: {type(gender)}")
            print(f"Annual Income: {annual_income}, type: {type(annual_income)}")
            print(f"Total Assets: {total_assets}, type: {type(total_assets)}")

            # Validate all required fields are present
            if not all([age, gender, annual_income, total_assets]):
                missing_fields = []
                if not age: missing_fields.append("age")
                if not gender: missing_fields.append("gender")
                if not annual_income: missing_fields.append("annual income")
                if not total_assets: missing_fields.append("total assets")
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                print(f"Validation Error: {error_msg}")
                return render_template("advice.html", r=error_msg)

            # Debug Step 3: Configure API
            print("\n==== API Configuration ====")
            api_key = "AIzaSyDtgxpFE0405T7m7l4llYVzW-eCb_Z-XMg"  # Replace with your actual key
            if not api_key:
                print("Error: No API key provided")
                return render_template("advice.html", r="API key is missing")
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-pro")
            print("API configured successfully")

            # Debug Step 4: Create prompt
            prompt = f"""
            As a financial advisor, provide specific investment advice for an investor with the following profile:

            Demographics:
            - Age: {age}
            - Gender: {gender}

            Financial Status:
            - Annual Income: ${annual_income}
            - Total Assets: ${total_assets}

            Please provide:
            1. Asset allocation recommendation based on age and financial status
            2. Specific investment suggestions considering the financial profile
            3. Timeline-based investment strategy
            4. Risk considerations and diversification advice
            """

            print("\n==== Generated Prompt ====")
            print(prompt)

            # Debug Step 5: Generate response
            response = model.generate_content(prompt)
            print("Response received from API")
            
            if response and hasattr(response, 'text'):
                advice_text = response.text
                print(f"Generated text length: {len(advice_text)}")
                print("Full advice text:", advice_text)
                
                # Return JSON response for AJAX
                return jsonify({"advice": advice_text})
            else:
                error_msg = "Invalid response format from API"
                print(f"Error: {error_msg}")
                return jsonify({"advice": error_msg})
                
        except Exception as e:
            error_msg = f"Server error: {str(e)}"
            print(f"Server Error: {error_msg}")
            return jsonify({"advice": error_msg})

    return render_template("financial_planning.html")

@app.route("/advice")
def advice():
    advice_text = request.args.get('advice', 'No advice available.')
    return render_template("advice.html", advice=advice_text)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except:
            flash('Username or email already exists.')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)