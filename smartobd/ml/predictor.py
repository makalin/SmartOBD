"""
Maintenance prediction using machine learning
"""

import time
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score

from ..core.logger import LoggerMixin
from ..core.config import Config


class MaintenancePredictor(LoggerMixin):
    """Maintenance prediction using machine learning"""
    
    def __init__(self, config: Config, db_manager):
        """
        Initialize maintenance predictor
        
        Args:
            config: Application configuration
            db_manager: Database manager instance
        """
        self.config = config
        self.db_manager = db_manager
        
        # ML settings
        ml_params = config.get_ml_params()
        self.model_path = Path(ml_params['model_path'])
        self.training_data_path = Path(ml_params['training_data_path'])
        self.prediction_interval_hours = ml_params['prediction_interval_hours']
        self.confidence_threshold = ml_params['confidence_threshold']
        self.features = ml_params['features']
        
        # Create directories
        self.model_path.mkdir(parents=True, exist_ok=True)
        self.training_data_path.mkdir(parents=True, exist_ok=True)
        
        # Models
        self.maintenance_models = {}
        self.scalers = {}
        self.last_prediction_time = None
        
        # Load existing models
        self._load_models()
        
        self.logger.info("Maintenance predictor initialized")
    
    def _load_models(self):
        """Load trained models from disk"""
        try:
            for maintenance_type in ['oil_change', 'tire_rotation', 'brake_check', 'air_filter']:
                model_file = self.model_path / f"{maintenance_type}_model.pkl"
                scaler_file = self.model_path / f"{maintenance_type}_scaler.pkl"
                
                if model_file.exists() and scaler_file.exists():
                    with open(model_file, 'rb') as f:
                        self.maintenance_models[maintenance_type] = pickle.load(f)
                    
                    with open(scaler_file, 'rb') as f:
                        self.scalers[maintenance_type] = pickle.load(f)
                    
                    self.logger.info(f"Loaded model for {maintenance_type}")
                else:
                    self.logger.info(f"No trained model found for {maintenance_type}")
                    
        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
    
    def _save_model(self, maintenance_type: str, model, scaler):
        """Save trained model to disk"""
        try:
            model_file = self.model_path / f"{maintenance_type}_model.pkl"
            scaler_file = self.model_path / f"{maintenance_type}_scaler.pkl"
            
            with open(model_file, 'wb') as f:
                pickle.dump(model, f)
            
            with open(scaler_file, 'wb') as f:
                pickle.dump(scaler, f)
            
            self.logger.info(f"Saved model for {maintenance_type}")
            
        except Exception as e:
            self.logger.error(f"Error saving model for {maintenance_type}: {e}")
    
    def train_models(self, vehicle_id: Optional[str] = None):
        """
        Train maintenance prediction models
        
        Args:
            vehicle_id: Optional vehicle ID to train for specific vehicle
        """
        try:
            self.logger.info("Starting model training...")
            
            # Get training data
            training_data = self._prepare_training_data(vehicle_id)
            
            if training_data.empty:
                self.logger.warning("No training data available")
                return
            
            # Train models for each maintenance type
            maintenance_types = ['oil_change', 'tire_rotation', 'brake_check', 'air_filter']
            
            for maintenance_type in maintenance_types:
                self._train_maintenance_model(maintenance_type, training_data)
            
            self.logger.info("Model training completed")
            
        except Exception as e:
            self.logger.error(f"Error training models: {e}")
    
    def _prepare_training_data(self, vehicle_id: Optional[str] = None) -> pd.DataFrame:
        """Prepare training data from OBD data and maintenance history"""
        try:
            # Get OBD data
            obd_data = self.db_manager.get_recent_obd_data(limit=10000)
            
            if not obd_data:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(obd_data)
            
            # Filter by vehicle if specified
            if vehicle_id:
                df = df[df['vehicle_id'] == vehicle_id]
            
            if df.empty:
                return df
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Sort by timestamp
            df = df.sort_values('timestamp')
            
            # Calculate features
            df = self._calculate_features(df)
            
            # Add maintenance labels (simplified - in practice you'd use actual maintenance history)
            df = self._add_maintenance_labels(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error preparing training data: {e}")
            return pd.DataFrame()
    
    def _calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate features from OBD data"""
        try:
            # Basic features
            features_df = df[['rpm', 'speed', 'engine_load', 'coolant_temp', 'intake_temp', 
                             'fuel_level', 'throttle_position', 'maf', 'fuel_pressure', 
                             'engine_oil_temp', 'engine_runtime']].copy()
            
            # Add rolling statistics
            for col in ['rpm', 'speed', 'engine_load']:
                if col in features_df.columns:
                    features_df[f'{col}_mean_1h'] = features_df[col].rolling(window=720).mean()  # 1 hour at 5s intervals
                    features_df[f'{col}_std_1h'] = features_df[col].rolling(window=720).std()
                    features_df[f'{col}_max_1h'] = features_df[col].rolling(window=720).max()
            
            # Add time-based features
            features_df['hour'] = df['timestamp'].dt.hour
            features_df['day_of_week'] = df['timestamp'].dt.dayofweek
            features_df['month'] = df['timestamp'].dt.month
            
            # Add distance-based features (simplified)
            if 'distance_since_dtc_clear' in df.columns:
                features_df['distance_since_dtc_clear'] = df['distance_since_dtc_clear']
            
            # Fill NaN values
            features_df = features_df.fillna(method='ffill').fillna(0)
            
            return features_df
            
        except Exception as e:
            self.logger.error(f"Error calculating features: {e}")
            return df
    
    def _add_maintenance_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add maintenance labels to training data (simplified)"""
        try:
            # This is a simplified approach - in practice you'd use actual maintenance history
            # For now, we'll create synthetic labels based on distance and time
            
            # Oil change labels (every 5000 miles)
            df['oil_change_needed'] = ((df['distance_since_dtc_clear'] % 5000) < 100).astype(int)
            
            # Tire rotation labels (every 7500 miles)
            df['tire_rotation_needed'] = ((df['distance_since_dtc_clear'] % 7500) < 100).astype(int)
            
            # Brake check labels (every 15000 miles)
            df['brake_check_needed'] = ((df['distance_since_dtc_clear'] % 15000) < 100).astype(int)
            
            # Air filter labels (every 30000 miles)
            df['air_filter_needed'] = ((df['distance_since_dtc_clear'] % 30000) < 100).astype(int)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error adding maintenance labels: {e}")
            return df
    
    def _train_maintenance_model(self, maintenance_type: str, training_data: pd.DataFrame):
        """Train model for specific maintenance type"""
        try:
            label_col = f'{maintenance_type}_needed'
            
            if label_col not in training_data.columns:
                self.logger.warning(f"No labels found for {maintenance_type}")
                return
            
            # Prepare features and labels
            feature_cols = [col for col in training_data.columns if col not in 
                          ['id', 'timestamp', 'vehicle_id', 'raw_data', 'oil_change_needed', 
                           'tire_rotation_needed', 'brake_check_needed', 'air_filter_needed']]
            
            X = training_data[feature_cols].values
            y = training_data[label_col].values
            
            # Remove rows with NaN values
            mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
            X = X[mask]
            y = y[mask]
            
            if len(X) < 100:
                self.logger.warning(f"Insufficient training data for {maintenance_type}")
                return
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            self.logger.info(f"Model for {maintenance_type} - Accuracy: {accuracy:.3f}")
            
            # Save model
            self.maintenance_models[maintenance_type] = model
            self.scalers[maintenance_type] = scaler
            self._save_model(maintenance_type, model, scaler)
            
        except Exception as e:
            self.logger.error(f"Error training model for {maintenance_type}: {e}")
    
    def run_predictions(self):
        """Run maintenance predictions"""
        try:
            self.logger.debug("Running maintenance predictions...")
            
            # Get recent OBD data
            recent_data = self.db_manager.get_recent_obd_data(limit=1000)
            
            if not recent_data:
                self.logger.debug("No recent data available for predictions")
                return
            
            # Prepare features
            features = self._prepare_prediction_features(recent_data)
            
            if features is None:
                return
            
            # Make predictions for each maintenance type
            predictions = {}
            
            for maintenance_type in ['oil_change', 'tire_rotation', 'brake_check', 'air_filter']:
                if maintenance_type in self.maintenance_models:
                    prediction = self._predict_maintenance(maintenance_type, features)
                    if prediction:
                        predictions[maintenance_type] = prediction
            
            # Update last prediction time
            self.last_prediction_time = datetime.now()
            
            # Save predictions to database
            self._save_predictions(predictions)
            
            self.logger.debug(f"Completed predictions: {len(predictions)} maintenance types")
            
        except Exception as e:
            self.logger.error(f"Error running predictions: {e}")
    
    def _prepare_prediction_features(self, recent_data: List[Dict[str, Any]]) -> Optional[np.ndarray]:
        """Prepare features for prediction"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame(recent_data)
            
            if df.empty:
                return None
            
            # Convert timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Calculate features (same as training)
            features_df = self._calculate_features(df)
            
            # Get latest features
            latest_features = features_df.iloc[-1:].values
            
            return latest_features
            
        except Exception as e:
            self.logger.error(f"Error preparing prediction features: {e}")
            return None
    
    def _predict_maintenance(self, maintenance_type: str, features: np.ndarray) -> Optional[Dict[str, Any]]:
        """Predict maintenance for specific type"""
        try:
            if maintenance_type not in self.maintenance_models:
                return None
            
            model = self.maintenance_models[maintenance_type]
            scaler = self.scalers[maintenance_type]
            
            # Scale features
            features_scaled = scaler.transform(features)
            
            # Make prediction
            prediction = model.predict(features_scaled)[0]
            probability = model.predict_proba(features_scaled)[0]
            
            # Get confidence
            confidence = max(probability)
            
            if confidence < self.confidence_threshold:
                return None
            
            return {
                'type': maintenance_type,
                'prediction': bool(prediction),
                'confidence': confidence,
                'probability': probability.tolist()
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting {maintenance_type}: {e}")
            return None
    
    def _save_predictions(self, predictions: Dict[str, Dict[str, Any]]):
        """Save predictions to database"""
        try:
            for maintenance_type, prediction in predictions.items():
                if prediction['prediction']:
                    # Create maintenance alert
                    alert_data = {
                        'vehicle_id': 'unknown_vehicle',  # In practice, get from current vehicle
                        'type': maintenance_type,
                        'severity': 'medium',
                        'message': f'{maintenance_type.replace("_", " ").title()} maintenance needed',
                        'predicted_date': datetime.now().isoformat(),
                        'confidence': prediction['confidence'],
                        'is_resolved': False
                    }
                    
                    self.db_manager.save_maintenance_alert(alert_data)
            
        except Exception as e:
            self.logger.error(f"Error saving predictions: {e}")
    
    def get_predictions(self) -> Dict[str, Any]:
        """Get current maintenance predictions"""
        try:
            predictions = {}
            
            for maintenance_type in ['oil_change', 'tire_rotation', 'brake_check', 'air_filter']:
                if maintenance_type in self.maintenance_models:
                    predictions[maintenance_type] = {
                        'model_loaded': True,
                        'last_training': 'unknown'  # In practice, track training dates
                    }
                else:
                    predictions[maintenance_type] = {
                        'model_loaded': False,
                        'last_training': None
                    }
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error getting predictions: {e}")
            return {}
    
    def get_maintenance_alerts(self) -> List[Dict[str, Any]]:
        """Get current maintenance alerts"""
        try:
            return self.db_manager.get_maintenance_alerts(resolved=False)
        except Exception as e:
            self.logger.error(f"Error getting maintenance alerts: {e}")
            return []
    
    def get_last_prediction_time(self) -> Optional[datetime]:
        """Get last prediction time"""
        return self.last_prediction_time 