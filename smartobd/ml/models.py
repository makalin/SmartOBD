"""
Machine learning models for SmartOBD
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error, classification_report

from ..core.logger import LoggerMixin


class MaintenanceModel(LoggerMixin):
    """Base class for maintenance prediction models"""
    
    def __init__(self, model_type: str):
        """
        Initialize maintenance model
        
        Args:
            model_type: Type of maintenance (oil_change, tire_rotation, etc.)
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.accuracy = 0.0
        
        self.logger.info(f"Initialized {model_type} maintenance model")
    
    def train(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Train the model
        
        Args:
            X: Feature matrix
            y: Target values
            
        Returns:
            Model accuracy
        """
        try:
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test_scaled)
            self.accuracy = accuracy_score(y_test, y_pred)
            
            self.is_trained = True
            
            self.logger.info(f"{self.model_type} model trained with accuracy: {self.accuracy:.3f}")
            return self.accuracy
            
        except Exception as e:
            self.logger.error(f"Error training {self.model_type} model: {e}")
            return 0.0
    
    def predict(self, X: np.ndarray) -> Tuple[bool, float]:
        """
        Make prediction
        
        Args:
            X: Feature matrix
            
        Returns:
            Tuple of (prediction, confidence)
        """
        if not self.is_trained or self.model is None:
            return False, 0.0
        
        try:
            X_scaled = self.scaler.transform(X)
            prediction = self.model.predict(X_scaled)[0]
            probability = self.model.predict_proba(X_scaled)[0]
            confidence = max(probability)
            
            return bool(prediction), confidence
            
        except Exception as e:
            self.logger.error(f"Error making prediction: {e}")
            return False, 0.0
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance"""
        if not self.is_trained or self.model is None:
            return {}
        
        try:
            importance = self.model.feature_importances_
            # In practice, you'd have feature names
            feature_names = [f"feature_{i}" for i in range(len(importance))]
            
            return dict(zip(feature_names, importance))
            
        except Exception as e:
            self.logger.error(f"Error getting feature importance: {e}")
            return {}


class AnomalyDetector(LoggerMixin):
    """Anomaly detection for OBD data"""
    
    def __init__(self):
        """Initialize anomaly detector"""
        self.model = None
        self.scaler = StandardScaler()
        self.threshold = 0.95
        self.is_trained = False
        
        self.logger.info("Anomaly detector initialized")
    
    def train(self, data: np.ndarray):
        """
        Train anomaly detector
        
        Args:
            data: Normal OBD data for training
        """
        try:
            # Scale data
            data_scaled = self.scaler.fit_transform(data)
            
            # Use Isolation Forest for anomaly detection
            from sklearn.ensemble import IsolationForest
            
            self.model = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            
            self.model.fit(data_scaled)
            self.is_trained = True
            
            self.logger.info("Anomaly detector trained successfully")
            
        except Exception as e:
            self.logger.error(f"Error training anomaly detector: {e}")
    
    def detect_anomalies(self, data: np.ndarray) -> np.ndarray:
        """
        Detect anomalies in data
        
        Args:
            data: OBD data to check for anomalies
            
        Returns:
            Boolean array indicating anomalies
        """
        if not self.is_trained or self.model is None:
            return np.zeros(len(data), dtype=bool)
        
        try:
            data_scaled = self.scaler.transform(data)
            predictions = self.model.predict(data_scaled)
            
            # Isolation Forest returns -1 for anomalies, 1 for normal
            anomalies = predictions == -1
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
            return np.zeros(len(data), dtype=bool)
    
    def get_anomaly_score(self, data: np.ndarray) -> np.ndarray:
        """
        Get anomaly scores
        
        Args:
            data: OBD data
            
        Returns:
            Array of anomaly scores
        """
        if not self.is_trained or self.model is None:
            return np.zeros(len(data))
        
        try:
            data_scaled = self.scaler.transform(data)
            scores = self.model.decision_function(data_scaled)
            
            return scores
            
        except Exception as e:
            self.logger.error(f"Error getting anomaly scores: {e}")
            return np.zeros(len(data)) 