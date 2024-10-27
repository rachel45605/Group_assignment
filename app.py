from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/financial-planning', methods=['GET', 'POST'])
def financial_planning():
    if request.method == 'POST':
        # Get form data
        user_id = session.get('user_id', 1)  # Default to 1 for testing
        data = {
            'age': request.form.get('age'),
            'gender': request.form.get('gender'),
            'annual_income': request.form.get('annual_income'),
            'risk_level': request.form.get('risk_level'),
            'investment_horizon': request.form.get('investment_horizon'),
            'region': request.form.get('region'),
            'total_assets': request.form.get('total_assets'),
            'selected_portfolios': request.form.getlist('portfolios[]')
        }
        
        # Create new financial profile
        profile = FinancialProfile(
            user_id=user_id,
            age=data['age'],
            gender=data['gender'],
            annual_income=float(data['annual_income']),
            risk_level=data['risk_level'],
            investment_horizon=data['investment_horizon'],
            region=data['region'],
            total_assets=float(data['total_assets']),
            selected_portfolios=','.join(data['selected_portfolios'])
        )
        
        try:
            db.session.add(profile)
            db.session.commit()
            
            # Generate advice based on profile
            advice = generate_financial_advice(data)
            return jsonify({
                'status': 'success',
                'advice': advice
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    # For GET request, render the form
    return render_template('financial_planning.html')

def generate_financial_advice(data):
    # Simple advice generation based on risk level and investment horizon
    risk_level = data['risk_level']
    horizon = data['investment_horizon']
    income = float(data['annual_income'])
    
    advice = f"""
    Based on your profile:
    
    1. Investment Strategy:
    - Risk Profile: {risk_level.capitalize()}
    - Time Horizon: {horizon.capitalize()}
    - Recommended Monthly Investment: ${round(income * 0.2 / 12, 2)}
    
    2. Portfolio Recommendations:
    """
    
    if risk_level == 'conservative':
        advice += """
    - 60% Global Bonds
    - 30% Blue-chip stocks
    - 10% Cash equivalents
        """
    elif risk_level == 'moderate':
        advice += """
    - 40% Growth stocks
    - 30% Value stocks
    - 20% Bonds
    - 10% REITs
        """
    else:  # aggressive
        advice += """
    - 50% Growth stocks
    - 30% Emerging markets
    - 15% Tech sector
    - 5% Crypto/High-risk assets
        """
    
    return advice

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

# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)