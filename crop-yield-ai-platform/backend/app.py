from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, Length
from email_validator import validate_email, EmailNotValidError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import requests
import joblib
import numpy as np
import pandas as pd
from PIL import Image
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))
from enhanced_prediction import CropYieldPredictor

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crop_yield_platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = '../data/uploads'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize enhanced prediction model
predictor = CropYieldPredictor()

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    regional_language = db.Column(db.String(50), default='english')
    birthday = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Field(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    field_name = db.Column(db.String(100))
    soil_condition = db.Column(db.String(200))
    weather_condition = db.Column(db.String(200))
    field_image = db.Column(db.String(200))
    last_year_profit = db.Column(db.Float)
    field_type = db.Column(db.String(50))
    area_hectares = db.Column(db.Float)
    crop_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    field_id = db.Column(db.Integer, db.ForeignKey('field.id'), nullable=True)
    crop_type = db.Column(db.String(50))
    predicted_yield = db.Column(db.Float)
    confidence = db.Column(db.Float)
    recommendations = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    name = StringField('Full Name', validators=[DataRequired()])
    address = StringField('Address')
    regional_language = SelectField('Preferred Language', 
                                  choices=[('english', 'English'), ('hindi', 'Hindi'), ('odia', 'Odia')])

class FieldForm(FlaskForm):
    field_name = StringField('Field Name', validators=[DataRequired()])
    soil_condition = TextAreaField('Soil Condition')
    weather_condition = StringField('Weather Condition')
    last_year_profit = FloatField('Last Year Profit (₹)')
    field_type = SelectField('Field Type', 
                           choices=[('paddy', 'Paddy'), ('wheat', 'Wheat'), ('sugarcane', 'Sugarcane'), 
                                  ('cotton', 'Cotton'), ('maize', 'Maize')])
    area_hectares = FloatField('Area (Hectares)', validators=[DataRequired()])
    crop_type = SelectField('Current Crop Type',
                          choices=[('rice', 'Rice'), ('wheat', 'Wheat'), ('sugarcane', 'Sugarcane'),
                                 ('cotton', 'Cotton'), ('maize', 'Maize')])

# Language Support
def load_translations():
    translations = {}
    try:
        with open('data/translations.json', 'r', encoding='utf-8') as f:
            translations = json.load(f)
    except FileNotFoundError:
        translations = {
            'english': {},
            'hindi': {},
            'odia': {}
        }
    return translations

def get_translation(key, language='english'):
    translations = load_translations()
    return translations.get(language, {}).get(key, key)

# ML Model Functions
def load_yield_model():
    try:
        model = joblib.load('models/yield_prediction_model.pkl')
        return model
    except FileNotFoundError:
        return None

def create_dummy_model():
    """Create a dummy model for demonstration"""
    from sklearn.ensemble import RandomForestRegressor
    
    # Create dummy training data
    X_dummy = np.random.rand(1000, 6)  # 6 features
    y_dummy = np.random.rand(1000) * 10 + 2  # Yield between 2-12 tons/hectare
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_dummy, y_dummy)
    
    # Save the model
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/yield_prediction_model.pkl')
    return model

def predict_yield_enhanced(crop_type, area, rainfall, temperature, soil_ph, fertilizer_usage, pest_control):
    """Enhanced yield prediction using the improved ML model"""
    try:
        # Load models if not already loaded
        if not predictor.models:
            predictor.load_models()
        
        # Make prediction
        predicted_yield, confidence, model_predictions = predictor.predict_yield(
            crop_type, area, rainfall, temperature, soil_ph, fertilizer_usage, pest_control
        )
        
        return predicted_yield, confidence, model_predictions
    except Exception as e:
        print(f"Enhanced prediction error: {e}")
        # Fallback to simple prediction
        return predictor._fallback_prediction(
            crop_type, area, rainfall, temperature, soil_ph, fertilizer_usage, pest_control
        )

def get_enhanced_recommendations(crop_type, predicted_yield, area, rainfall, temperature, 
                               soil_ph, fertilizer_usage, pest_control, soil_condition="", 
                               weather_condition=""):
    """Get enhanced recommendations using the improved model"""
    try:
        return predictor.get_recommendations(
            crop_type, predicted_yield, area, rainfall, temperature, 
            soil_ph, fertilizer_usage, pest_control, soil_condition, weather_condition
        )
    except Exception as e:
        print(f"Recommendations error: {e}")
        # Fallback to simple recommendations
        recommendations = []
        
        if predicted_yield < 3:
            recommendations.append("Low yield predicted - consider soil testing and improved practices")
        elif predicted_yield < 5:
            recommendations.append("Moderate yield expected - focus on optimization")
        else:
            recommendations.append("Good yield potential - maintain current practices")
            
        return [{'message': rec, 'priority': 'medium', 'category': 'general'} for rec in recommendations]

def get_market_insights(crop_type, predicted_yield, area):
    """Get market insights and profit projections"""
    try:
        return predictor.get_market_insights(crop_type, predicted_yield, area)
    except Exception as e:
        print(f"Market insights error: {e}")
        return {
            'crop_type': crop_type,
            'predicted_yield': predicted_yield,
            'area': area,
            'net_profit': 0,
            'profit_margin': 0
        }

# Routes
@app.route('/')
def index():
    return render_template('interactive_index.html')

@app.route('/simple')
def simple_index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists')
            return render_template('register.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            name=form.name.data,
            address=form.address.data,
            regional_language=form.regional_language.data
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    fields = Field.query.filter_by(user_id=current_user.id).all()
    recent_predictions = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.created_at.desc()).limit(5).all()
    return render_template('interactive_dashboard.html', fields=fields, predictions=recent_predictions)

@app.route('/dashboard/simple')
@login_required
def simple_dashboard():
    fields = Field.query.filter_by(user_id=current_user.id).all()
    recent_predictions = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.created_at.desc()).limit(5).all()
    return render_template('dashboard.html', fields=fields, predictions=recent_predictions)

@app.route('/add_field', methods=['GET', 'POST'])
@login_required
def add_field():
    form = FieldForm()
    if form.validate_on_submit():
        field = Field(
            user_id=current_user.id,
            field_name=form.field_name.data,
            soil_condition=form.soil_condition.data,
            weather_condition=form.weather_condition.data,
            last_year_profit=form.last_year_profit.data,
            field_type=form.field_type.data,
            area_hectares=form.area_hectares.data,
            crop_type=form.crop_type.data
        )
        db.session.add(field)
        db.session.commit()
        flash('Field added successfully')
        return redirect(url_for('dashboard'))
    return render_template('add_field.html', form=form)

@app.route('/predict_yield', methods=['GET', 'POST'])
def predict_yield_route():
    if request.method == 'POST':
        try:
            # Get form data
            crop_type = request.form.get('crop_type', 'rice')
            area = float(request.form.get('area', 1))
            rainfall = float(request.form.get('rainfall', 1000))
            temperature = float(request.form.get('temperature', 25))
            soil_ph = float(request.form.get('soil_ph', 7))
            fertilizer_usage = float(request.form.get('fertilizer_usage', 50))
            pest_control = float(request.form.get('pest_control', 1))
            
            # Make enhanced prediction
            predicted_yield, confidence, model_predictions = predict_yield_enhanced(
                crop_type, area, rainfall, temperature, soil_ph, fertilizer_usage, pest_control
            )
            
            # Generate enhanced recommendations
            soil_condition = request.form.get('soil_condition', '')
            weather_condition = request.form.get('weather_condition', '')
            recommendations = get_enhanced_recommendations(
                crop_type, predicted_yield, area, rainfall, temperature, 
                soil_ph, fertilizer_usage, pest_control, soil_condition, weather_condition
            )
            
            # Get market insights
            market_insights = get_market_insights(crop_type, predicted_yield, area)
            
            # Save prediction
            prediction = Prediction(
                user_id=current_user.id if current_user.is_authenticated else None,
                crop_type=crop_type,
                predicted_yield=predicted_yield,
                confidence=confidence,
                recommendations=json.dumps(recommendations)
            )
            db.session.add(prediction)
            db.session.commit()
            
            result = {
                'predicted_yield': round(predicted_yield, 2),
                'confidence': round(confidence * 100, 1),
                'recommendations': recommendations,
                'crop_type': crop_type,
                'area': area,
                'model_predictions': model_predictions,
                'market_insights': market_insights
            }
            
            # Store result in session for enhanced results page
            session['prediction_result'] = result
            return redirect(url_for('prediction_result'))
            
        except Exception as e:
            flash(f'Error making prediction: {str(e)}')
            
    return render_template('enhanced_interactive_predict.html')

@app.route('/prediction-result')
def prediction_result():
    """Display enhanced prediction result with visualizations"""
    result = session.get('prediction_result')
    if not result:
        flash('No prediction results found. Please make a prediction first.', 'warning')
        return redirect(url_for('predict_yield_route'))
    
    return render_template('enhanced_prediction_result.html', result=result)

@app.route('/universal_predict', methods=['GET', 'POST'])
def universal_predict():
    # Universal prediction without login
    return render_template('universal_predict.html')

@app.route('/api/weather')
def get_weather():
    # Dummy weather data - in real implementation, integrate with weather API
    weather_data = {
        'temperature': 28.5,
        'humidity': 75,
        'rainfall_forecast': 25.4,
        'wind_speed': 12.3,
        'alert': 'Heavy rainfall expected in next 48 hours'
    }
    return jsonify(weather_data)

@app.route('/api/market_prices')
def get_market_prices():
    # Dummy market price data
    prices = {
        'rice': {'price': 2500, 'unit': 'per quintal', 'trend': 'up'},
        'wheat': {'price': 2200, 'unit': 'per quintal', 'trend': 'stable'},
        'sugarcane': {'price': 350, 'unit': 'per quintal', 'trend': 'down'},
        'cotton': {'price': 6800, 'unit': 'per quintal', 'trend': 'up'},
        'maize': {'price': 1800, 'unit': 'per quintal', 'trend': 'up'}
    }
    return jsonify(prices)

@app.route('/cost_benefit')
def cost_benefit_calculator():
    return render_template('cost_benefit.html')

@app.route('/help')
def help_system():
    return render_template('help.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)