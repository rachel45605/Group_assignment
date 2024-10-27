from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai
import os
from datetime import datetime
import os



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
        try:
            # Configure Gemini AI
            genai.configure(api_key="AIzaSyDtgxpFE0405T7m7l4llYVzW-eCb_Z-XMg")  # Replace with your API key
            model = genai.GenerativeModel("gemini-pro")

            # Get form data
            age = request.form.get("age")
            gender = request.form.get("gender")
            annual_income = request.form.get("annual_income")
            total_assets = request.form.get("total_assets")
            risk_level = request.form.get("risk_level")
            investment_horizon = request.form.get("investment_horizon")
            portfolios = request.form.getlist("portfolios[]")

            # Create the prompt
            prompt = f"""
            As a financial advisor, provide specific investment advice for an investor with the following profile:

            Demographics:
            - Age: {age}
            - Gender: {gender}

            Financial Status:
            - Annual Income: ${annual_income}
            - Total Assets: ${total_assets}

            Investment Preferences:
            - Risk Tolerance: {risk_level}
            - Investment Horizon: {investment_horizon}
            - Interested Portfolios: {', '.join(portfolios)}

            Please provide:
            1. Asset allocation recommendation
            2. Specific investment suggestions based on their risk level
            3. Timeline-based investment strategy
            4. Key considerations and risks
            """

            try:
                # Generate response
                response = model.generate_content(prompt)
                if response and hasattr(response, 'text'):
                    return render_template("advice.html", r=response.text)
                else:
                    return render_template("advice.html", r="Sorry, couldn't generate advice at this time.")
            
            except Exception as e:
                app.logger.error(f"Error generating advice: {str(e)}")
                return render_template("advice.html", r=f"Error generating advice: {str(e)}")

        except Exception as e:
            app.logger.error(f"Error in financial_planning: {str(e)}")
            return render_template("advice.html", r=f"An error occurred: {str(e)}")

    # GET request - show the form
    return render_template("financial_planning.html")

@app.route("/advice")
def advice():
    advice_text = request.args.get('r', 'No advice available.')
    return render_template("advice.html", r=advice_text)


# @app.route('/financial-planning', methods=['GET', 'POST'])
# def financial_planning():
#     if request.method == 'POST':
#         # Get form data
#         user_id = session.get('user_id', 1)  # Default to 1 for testing
#         data = {
#             'age': request.form.get('age'),
#             'gender': request.form.get('gender'),
#             'annual_income': request.form.get('annual_income'),
#             'risk_level': request.form.get('risk_level'),
#             'investment_horizon': request.form.get('investment_horizon'),
#             'region': request.form.get('region'),
#             'total_assets': request.form.get('total_assets'),
#             'selected_portfolios': request.form.getlist('portfolios[]')
#         }
        
#         # Create new financial profile
#         profile = FinancialProfile(
#             user_id=user_id,
#             age=data['age'],
#             gender=data['gender'],
#             annual_income=float(data['annual_income']),
#             risk_level=data['risk_level'],
#             investment_horizon=data['investment_horizon'],
#             region=data['region'],
#             total_assets=float(data['total_assets']),
#             selected_portfolios=','.join(data['selected_portfolios'])
#         )
        
#         try:
#             db.session.add(profile)
#             db.session.commit()
            
#             # Generate advice based on profile
#             advice = generate_financial_advice(data)
#             return jsonify({
#                 'status': 'success',
#                 'advice': advice
#             })
#         except Exception as e:
#             db.session.rollback()
#             return jsonify({
#                 'status': 'error',
#                 'message': str(e)
#             }), 500
    
#     # For GET request, render the form
#     return render_template('financial_planning.html')

# def generate_financial_advice(data):
#     # Simple advice generation based on risk level and investment horizon
#     risk_level = data['risk_level']
#     horizon = data['investment_horizon']
#     income = float(data['annual_income'])
    
#     advice = f"""
#     Based on your profile:
    
#     1. Investment Strategy:
#     - Risk Profile: {risk_level.capitalize()}
#     - Time Horizon: {horizon.capitalize()}
#     - Recommended Monthly Investment: ${round(income * 0.2 / 12, 2)}
    
#     2. Portfolio Recommendations:
#     """
    
#     if risk_level == 'conservative':
#         advice += """
#     - 60% Global Bonds
#     - 30% Blue-chip stocks
#     - 10% Cash equivalents
#         """
#     elif risk_level == 'moderate':
#         advice += """
#     - 40% Growth stocks
#     - 30% Value stocks
#     - 20% Bonds
#     - 10% REITs
#         """
#     else:  # aggressive
#         advice += """
#     - 50% Growth stocks
#     - 30% Emerging markets
#     - 15% Tech sector
#     - 5% Crypto/High-risk assets
#         """
    
#     return advice

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

# @app.route('/advice', methods=['POST'])
# def advice():
#     # Get data from the form submission
#     age = request.form.get('age')
#     gender = request.form.get('gender')
#     annual_income = request.form.get('annual_income')
#     total_assets = request.form.get('total_assets')
#     risk_level = request.form.get('risk_level')
#     investment_horizon = request.form.get('investment_horizon')
#     region = request.form.get('region')
#     selected_portfolios = request.form.getlist('portfolios[]')

#     # Here you would call your logic to generate advice based on the input
#     advice_text = generate_advice(age, gender, annual_income, total_assets, risk_level, investment_horizon, region, selected_portfolios)

#     return jsonify({'advice': advice_text})

# def generate_advice(age, gender, annual_income, total_assets, risk_level, investment_horizon, region, selected_portfolios):
#     # Placeholder logic for advice generation
#     return f"Based on your profile:\n- Age: {age}\n- Gender: {gender}\n- Annual Income: {annual_income}\n- Total Assets: {total_assets}\n- Risk Level: {risk_level}\n- Investment Horizon: {investment_horizon}\n- Region: {region}\n- Selected Portfolios: {', '.join(selected_portfolios)}\n\nHere are your personalized investment strategies..."

if __name__ == "__main__":
    app.run(debug=True)