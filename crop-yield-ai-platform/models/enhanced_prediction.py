import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import json
import os
from datetime import datetime

class CropYieldPredictor:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.label_encoders = {}
        self.feature_columns = [
            'area', 'rainfall', 'temperature', 'soil_ph', 
            'fertilizer_usage', 'pest_control', 'crop_type_encoded'
        ]
        self.crop_types = ['rice', 'wheat', 'sugarcane', 'cotton', 'maize']
        
    def generate_synthetic_data(self, n_samples=5000):
        """Generate realistic synthetic agricultural data"""
        np.random.seed(42)
        
        data = []
        for _ in range(n_samples):
            crop = np.random.choice(self.crop_types)
            
            # Realistic parameter ranges based on crop type
            crop_params = {
                'rice': {
                    'rainfall': (800, 2500),
                    'temperature': (20, 35),
                    'soil_ph': (5.5, 7.5),
                    'base_yield': (3, 8)
                },
                'wheat': {
                    'rainfall': (300, 800),
                    'temperature': (15, 25),
                    'soil_ph': (6.0, 8.0),
                    'base_yield': (2, 6)
                },
                'sugarcane': {
                    'rainfall': (1000, 2000),
                    'temperature': (25, 35),
                    'soil_ph': (6.5, 7.5),
                    'base_yield': (40, 80)
                },
                'cotton': {
                    'rainfall': (500, 1200),
                    'temperature': (20, 32),
                    'soil_ph': (5.5, 8.0),
                    'base_yield': (1, 4)
                },
                'maize': {
                    'rainfall': (600, 1200),
                    'temperature': (18, 32),
                    'soil_ph': (6.0, 7.5),
                    'base_yield': (3, 9)
                }
            }
            
            params = crop_params[crop]
            
            area = np.random.uniform(0.5, 20)
            rainfall = np.random.uniform(*params['rainfall'])
            temperature = np.random.uniform(*params['temperature'])
            soil_ph = np.random.uniform(*params['soil_ph'])
            fertilizer_usage = np.random.uniform(20, 150)
            pest_control = np.random.randint(1, 11)
            
            # Calculate base yield
            base_yield = np.random.uniform(*params['base_yield'])
            
            # Apply realistic factors
            rainfall_factor = self._calculate_rainfall_factor(rainfall, crop)
            temp_factor = self._calculate_temperature_factor(temperature, crop)
            ph_factor = self._calculate_ph_factor(soil_ph, crop)
            fertilizer_factor = self._calculate_fertilizer_factor(fertilizer_usage)
            pest_factor = pest_control / 10.0
            
            # Calculate final yield with some randomness
            yield_multiplier = (
                rainfall_factor * temp_factor * ph_factor * 
                fertilizer_factor * pest_factor
            )
            
            predicted_yield = base_yield * yield_multiplier * np.random.uniform(0.8, 1.2)
            predicted_yield = max(0.1, predicted_yield)  # Ensure positive yield
            
            data.append({
                'crop_type': crop,
                'area': area,
                'rainfall': rainfall,
                'temperature': temperature,
                'soil_ph': soil_ph,
                'fertilizer_usage': fertilizer_usage,
                'pest_control': pest_control,
                'yield': predicted_yield
            })
        
        return pd.DataFrame(data)
    
    def _calculate_rainfall_factor(self, rainfall, crop):
        """Calculate rainfall impact factor"""
        optimal_ranges = {
            'rice': (1200, 1800),
            'wheat': (400, 600),
            'sugarcane': (1200, 1600),
            'cotton': (600, 1000),
            'maize': (700, 1000)
        }
        
        optimal = optimal_ranges[crop]
        if optimal[0] <= rainfall <= optimal[1]:
            return 1.0
        elif rainfall < optimal[0]:
            return 0.3 + 0.7 * (rainfall / optimal[0])
        else:
            return 1.0 - 0.5 * ((rainfall - optimal[1]) / optimal[1])
    
    def _calculate_temperature_factor(self, temp, crop):
        """Calculate temperature impact factor"""
        optimal_ranges = {
            'rice': (25, 30),
            'wheat': (18, 22),
            'sugarcane': (26, 32),
            'cotton': (25, 30),
            'maize': (24, 28)
        }
        
        optimal = optimal_ranges[crop]
        if optimal[0] <= temp <= optimal[1]:
            return 1.0
        elif temp < optimal[0]:
            return 0.4 + 0.6 * (temp / optimal[0])
        else:
            return 1.0 - 0.4 * ((temp - optimal[1]) / 30)
    
    def _calculate_ph_factor(self, ph, crop):
        """Calculate pH impact factor"""
        optimal_ranges = {
            'rice': (6.0, 7.0),
            'wheat': (6.5, 7.5),
            'sugarcane': (6.5, 7.5),
            'cotton': (6.0, 7.5),
            'maize': (6.0, 7.0)
        }
        
        optimal = optimal_ranges[crop]
        if optimal[0] <= ph <= optimal[1]:
            return 1.0
        else:
            distance = min(abs(ph - optimal[0]), abs(ph - optimal[1]))
            return max(0.3, 1.0 - 0.2 * distance)
    
    def _calculate_fertilizer_factor(self, fertilizer):
        """Calculate fertilizer impact factor"""
        if fertilizer < 20:
            return 0.4 + 0.6 * (fertilizer / 20)
        elif fertilizer <= 100:
            return 1.0
        else:
            return 1.0 - 0.3 * ((fertilizer - 100) / 100)
    
    def train_models(self):
        """Train multiple ML models for prediction"""
        print("Generating synthetic training data...")
        df = self.generate_synthetic_data()
        
        # Prepare features
        le = LabelEncoder()
        df['crop_type_encoded'] = le.fit_transform(df['crop_type'])
        self.label_encoders['crop_type'] = le
        
        # Prepare features and target
        X = df[self.feature_columns].values
        y = df['yield'].values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['main'] = scaler
        
        # Train multiple models
        models_to_train = {
            'random_forest': RandomForestRegressor(
                n_estimators=100, 
                max_depth=10, 
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        }
        
        print("Training models...")
        for name, model in models_to_train.items():
            print(f"Training {name}...")
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_score = model.score(X_train_scaled, y_train)
            test_score = model.score(X_test_scaled, y_test)
            y_pred = model.predict(X_test_scaled)
            mae = mean_absolute_error(y_test, y_pred)
            
            print(f"{name} - Train R²: {train_score:.3f}, Test R²: {test_score:.3f}, MAE: {mae:.3f}")
            
            self.models[name] = model
        
        # Save models
        self._save_models()
        print("Models trained and saved successfully!")
    
    def _save_models(self):
        """Save trained models and scalers"""
        os.makedirs('models', exist_ok=True)
        
        for name, model in self.models.items():
            joblib.dump(model, f'models/{name}_model.pkl')
        
        for name, scaler in self.scalers.items():
            joblib.dump(scaler, f'models/{name}_scaler.pkl')
        
        for name, encoder in self.label_encoders.items():
            joblib.dump(encoder, f'models/{name}_encoder.pkl')
        
        # Save metadata
        metadata = {
            'feature_columns': self.feature_columns,
            'crop_types': self.crop_types,
            'models': list(self.models.keys()),
            'created_at': datetime.now().isoformat()
        }
        
        with open('models/metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def load_models(self):
        """Load trained models"""
        try:
            # Load metadata
            with open('models/metadata.json', 'r') as f:
                metadata = json.load(f)
            
            # Load models
            for model_name in metadata['models']:
                self.models[model_name] = joblib.load(f'models/{model_name}_model.pkl')
            
            # Load scalers
            self.scalers['main'] = joblib.load('models/main_scaler.pkl')
            
            # Load encoders
            self.label_encoders['crop_type'] = joblib.load('models/crop_type_encoder.pkl')
            
            print("Models loaded successfully!")
            return True
        except FileNotFoundError:
            print("No pre-trained models found. Training new models...")
            self.train_models()
            return True
        except Exception as e:
            print(f"Error loading models: {e}")
            return False
    
    def predict_yield(self, crop_type, area, rainfall, temperature, soil_ph, 
                     fertilizer_usage, pest_control):
        """Make yield prediction with ensemble of models"""
        try:
            # Prepare input data
            crop_encoded = self.label_encoders['crop_type'].transform([crop_type])[0]
            
            input_data = np.array([[
                area, rainfall, temperature, soil_ph, 
                fertilizer_usage, pest_control, crop_encoded
            ]])
            
            # Scale input
            input_scaled = self.scalers['main'].transform(input_data)
            
            # Make predictions with all models
            predictions = {}
            for name, model in self.models.items():
                pred = model.predict(input_scaled)[0]
                predictions[name] = max(0.1, pred)  # Ensure positive yield
            
            # Ensemble prediction (weighted average)
            ensemble_pred = np.mean(list(predictions.values()))
            
            # Calculate confidence based on model agreement
            pred_std = np.std(list(predictions.values()))
            confidence = max(0.6, min(0.98, 1.0 - (pred_std / ensemble_pred)))
            
            return ensemble_pred, confidence, predictions
            
        except Exception as e:
            print(f"Prediction error: {e}")
            # Fallback to simple prediction
            return self._fallback_prediction(crop_type, area, rainfall, temperature, 
                                           soil_ph, fertilizer_usage, pest_control)
    
    def _fallback_prediction(self, crop_type, area, rainfall, temperature, 
                           soil_ph, fertilizer_usage, pest_control):
        """Fallback prediction method"""
        base_yields = {
            'rice': 5.0,
            'wheat': 3.5,
            'sugarcane': 60.0,
            'cotton': 2.5,
            'maize': 6.0
        }
        
        base = base_yields.get(crop_type, 4.0)
        
        # Apply simple factors
        rainfall_factor = min(1.2, rainfall / 1000)
        temp_factor = 1.0 if 20 <= temperature <= 30 else 0.8
        ph_factor = 1.0 if 6.0 <= soil_ph <= 7.5 else 0.9
        fertilizer_factor = min(1.3, fertilizer_usage / 100)
        pest_factor = pest_control / 10.0
        
        yield_pred = (base * rainfall_factor * temp_factor * 
                     ph_factor * fertilizer_factor * pest_factor)
        
        return max(0.1, yield_pred), 0.75, {'fallback': yield_pred}
    
    def get_recommendations(self, crop_type, predicted_yield, area, rainfall, 
                          temperature, soil_ph, fertilizer_usage, pest_control, 
                          soil_condition="", weather_condition=""):
        """Generate detailed recommendations"""
        recommendations = []
        
        # Yield-based recommendations
        if predicted_yield < 3:
            recommendations.append({
                'category': 'yield_improvement',
                'priority': 'high',
                'message': 'Low yield predicted. Consider soil testing and nutrient management.',
                'action': 'Conduct comprehensive soil analysis and adjust fertilization strategy.'
            })
        elif predicted_yield < 5:
            recommendations.append({
                'category': 'yield_optimization',
                'priority': 'medium',
                'message': 'Moderate yield expected. Room for improvement through better practices.',
                'action': 'Focus on irrigation timing and pest monitoring.'
            })
        else:
            recommendations.append({
                'category': 'yield_maintenance',
                'priority': 'low',
                'message': 'Good yield potential. Maintain current practices.',
                'action': 'Continue with proven agricultural methods.'
            })
        
        # Specific factor recommendations
        if soil_ph < 6.0:
            recommendations.append({
                'category': 'soil_management',
                'priority': 'high',
                'message': f'Soil pH ({soil_ph}) is too acidic for optimal {crop_type} growth.',
                'action': 'Apply lime to increase soil pH to 6.5-7.5 range.'
            })
        elif soil_ph > 8.0:
            recommendations.append({
                'category': 'soil_management',
                'priority': 'high',
                'message': f'Soil pH ({soil_ph}) is too alkaline for {crop_type}.',
                'action': 'Apply sulfur or organic matter to reduce pH.'
            })
        
        if rainfall < 500:
            recommendations.append({
                'category': 'irrigation',
                'priority': 'high',
                'message': f'Low rainfall ({rainfall}mm) requires supplemental irrigation.',
                'action': 'Install drip irrigation system for efficient water use.'
            })
        elif rainfall > 2000:
            recommendations.append({
                'category': 'drainage',
                'priority': 'medium',
                'message': f'High rainfall ({rainfall}mm) may cause waterlogging.',
                'action': 'Ensure proper field drainage to prevent root damage.'
            })
        
        if fertilizer_usage < 30:
            recommendations.append({
                'category': 'nutrition',
                'priority': 'medium',
                'message': 'Low fertilizer usage may limit yield potential.',
                'action': f'Consider increasing fertilizer application to 80-120 kg/ha for {crop_type}.'
            })
        elif fertilizer_usage > 150:
            recommendations.append({
                'category': 'nutrition',
                'priority': 'medium',
                'message': 'Excessive fertilizer may cause nutrient imbalance.',
                'action': 'Reduce fertilizer application and focus on balanced NPK ratios.'
            })
        
        if pest_control < 5:
            recommendations.append({
                'category': 'pest_management',
                'priority': 'high',
                'message': 'Inadequate pest control may significantly reduce yield.',
                'action': 'Implement integrated pest management (IPM) strategies.'
            })
        
        # Weather-based recommendations
        if "dry" in weather_condition.lower():
            recommendations.append({
                'category': 'water_management',
                'priority': 'high',
                'message': 'Dry weather conditions require careful water management.',
                'action': 'Implement water conservation techniques and monitor soil moisture.'
            })
        
        if "pest" in soil_condition.lower():
            recommendations.append({
                'category': 'pest_management',
                'priority': 'high',
                'message': 'Pest issues identified in field conditions.',
                'action': 'Apply targeted pest control measures and monitor regularly.'
            })
        
        return recommendations
    
    def get_market_insights(self, crop_type, predicted_yield, area):
        """Generate market insights and profit projections"""
        # Current market prices (₹ per quintal)
        market_prices = {
            'rice': 2500,
            'wheat': 2200,
            'sugarcane': 350,
            'cotton': 6800,
            'maize': 1800
        }
        
        price = market_prices.get(crop_type, 2000)
        total_production = predicted_yield * area * 10  # Convert tons to quintals
        gross_revenue = total_production * price
        
        # Estimate costs (₹ per hectare)
        cost_estimates = {
            'rice': 35000,
            'wheat': 25000,
            'sugarcane': 45000,
            'cotton': 40000,
            'maize': 30000
        }
        
        total_cost = cost_estimates.get(crop_type, 30000) * area
        net_profit = gross_revenue - total_cost
        profit_margin = (net_profit / gross_revenue * 100) if gross_revenue > 0 else 0
        
        return {
            'crop_type': crop_type,
            'predicted_yield': predicted_yield,
            'area': area,
            'total_production': total_production,
            'market_price': price,
            'gross_revenue': gross_revenue,
            'total_cost': total_cost,
            'net_profit': net_profit,
            'profit_margin': profit_margin,
            'revenue_per_hectare': gross_revenue / area if area > 0 else 0,
            'cost_per_hectare': total_cost / area if area > 0 else 0
        }

# Initialize and train models if run directly
if __name__ == "__main__":
    predictor = CropYieldPredictor()
    predictor.train_models()