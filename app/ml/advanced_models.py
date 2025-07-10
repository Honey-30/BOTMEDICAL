"""
Advanced Machine Learning Pipeline for Healthcare Diagnosis
"""

import numpy as np
import pandas as pd
import pickle
import joblib
import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
import xgboost as xgb
import lightgbm as lgb
from scipy.stats import mode
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
from sentence_transformers import SentenceTransformer
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    """Structured prediction result."""
    disease: str
    probability: float
    confidence: str
    risk_level: str
    recommendations: List[str]
    follow_up: List[str]

@dataclass
class SymptomAnalysis:
    """Structured symptom analysis result."""
    symptoms: List[str]
    severity_score: float
    severity_level: str
    emergency_flag: bool
    body_systems_affected: List[str]
    symptom_patterns: Dict[str, Any]

class AdvancedSymptomChecker:
    """
    Advanced ML-based symptom checker with multiple models and ensemble prediction.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the advanced symptom checker."""
        self.config = config or {}
        self.models = {}
        self.encoders = {}
        self.scalers = {}
        self.vectorizers = {}
        
        # Model weights for ensemble
        self.model_weights = {
            'random_forest': 0.3,
            'gradient_boosting': 0.25,
            'xgboost': 0.25,
            'lightgbm': 0.2
        }
        
        # Load pre-trained NLP models if available
        self.use_advanced_nlp = self.config.get('use_advanced_nlp', True)
        if self.use_advanced_nlp:
            try:
                self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
                self.medical_ner = pipeline("ner", 
                    model="dmis-lab/biobert-base-cased-v1.2-ner", 
                    aggregation_strategy="simple")
                logger.info("Advanced NLP models loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load advanced NLP models: {e}")
                self.use_advanced_nlp = False
        
        # Load knowledge bases
        self.symptom_knowledge = self._load_symptom_knowledge()
        self.disease_knowledge = self._load_disease_knowledge()
        
        # Initialize emergency detection
        self.emergency_detector = EmergencyDetector()
        
        # Model performance tracking
        self.performance_metrics = {}
        
    def _load_symptom_knowledge(self) -> Dict[str, Any]:
        """Load symptom knowledge base."""
        try:
            knowledge_path = os.path.join('data', 'symptom_knowledge.json')
            if os.path.exists(knowledge_path):
                with open(knowledge_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load symptom knowledge: {e}")
        
        # Default knowledge base
        return {
            "fever": {
                "severity_weight": 6,
                "body_system": "immune",
                "emergency_threshold": 39.5,
                "related_symptoms": ["chills", "sweating", "headache"]
            },
            "chest_pain": {
                "severity_weight": 9,
                "body_system": "cardiovascular",
                "emergency_threshold": 7,
                "related_symptoms": ["shortness_of_breath", "dizziness", "nausea"]
            },
            "headache": {
                "severity_weight": 4,
                "body_system": "neurological",
                "emergency_threshold": 8,
                "related_symptoms": ["nausea", "sensitivity_to_light", "vision_problems"]
            }
        }
    
    def _load_disease_knowledge(self) -> Dict[str, Any]:
        """Load disease knowledge base."""
        try:
            knowledge_path = os.path.join('data', 'disease_knowledge.json')
            if os.path.exists(knowledge_path):
                with open(knowledge_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load disease knowledge: {e}")
        
        # Default knowledge base
        return {
            "common_cold": {
                "severity": "mild",
                "typical_duration": "7-10 days",
                "common_symptoms": ["runny_nose", "sneezing", "cough", "sore_throat"],
                "risk_factors": ["exposure_to_cold_virus", "weakened_immune_system"],
                "recommendations": ["rest", "hydration", "over_the_counter_medication"]
            },
            "influenza": {
                "severity": "moderate",
                "typical_duration": "5-7 days",
                "common_symptoms": ["fever", "body_aches", "fatigue", "cough"],
                "risk_factors": ["seasonal_exposure", "lack_of_vaccination"],
                "recommendations": ["rest", "antiviral_medication", "vaccination_prevention"]
            }
        }
    
    def train_ensemble_models(self, X: np.ndarray, y: np.ndarray, 
                            symptom_features: List[str]) -> Dict[str, Any]:
        """
        Train ensemble of ML models for symptom prediction.
        
        Args:
            X: Feature matrix
            y: Target labels
            symptom_features: List of symptom feature names
            
        Returns:
            Dictionary containing training results and metrics
        """
        logger.info("Starting ensemble model training...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        self.scalers['standard'] = StandardScaler()
        X_train_scaled = self.scalers['standard'].fit_transform(X_train)
        X_test_scaled = self.scalers['standard'].transform(X_test)
        
        # Train individual models
        models_config = {
            'random_forest': {
                'model': RandomForestClassifier(
                    n_estimators=200,
                    max_depth=15,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                ),
                'use_scaled': False
            },
            'gradient_boosting': {
                'model': GradientBoostingClassifier(
                    n_estimators=200,
                    learning_rate=0.1,
                    max_depth=6,
                    random_state=42
                ),
                'use_scaled': False
            },
            'xgboost': {
                'model': xgb.XGBClassifier(
                    n_estimators=200,
                    learning_rate=0.1,
                    max_depth=6,
                    random_state=42,
                    eval_metric='mlogloss'
                ),
                'use_scaled': False
            },
            'lightgbm': {
                'model': lgb.LGBMClassifier(
                    n_estimators=200,
                    learning_rate=0.1,
                    max_depth=6,
                    random_state=42,
                    verbose=-1
                ),
                'use_scaled': True
            }
        }
        
        training_results = {}
        
        for model_name, config in models_config.items():
            logger.info(f"Training {model_name}...")
            
            try:
                # Select appropriate data
                X_train_model = X_train_scaled if config['use_scaled'] else X_train
                X_test_model = X_test_scaled if config['use_scaled'] else X_test
                
                # Train model
                model = config['model']
                model.fit(X_train_model, y_train)
                
                # Make predictions
                y_pred = model.predict(X_test_model)
                y_pred_proba = model.predict_proba(X_test_model)
                
                # Calculate metrics
                accuracy = accuracy_score(y_test, y_pred)
                precision, recall, f1, _ = precision_recall_fscore_support(
                    y_test, y_pred, average='weighted'
                )
                
                # Cross-validation score
                cv_scores = cross_val_score(model, X_train_model, y_train, cv=5)
                
                # Store model and results
                self.models[model_name] = model
                training_results[model_name] = {
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1,
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std()
                }
                
                logger.info(f"{model_name} - Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
                
            except Exception as e:
                logger.error(f"Error training {model_name}: {e}")
                continue
        
        # Store feature names and label encoder
        self.feature_names = symptom_features
        self.label_encoder = LabelEncoder()
        self.label_encoder.fit(y)
        
        # Calculate ensemble performance
        if len(self.models) > 1:
            ensemble_pred = self._ensemble_predict(X_test_scaled, X_test)
            ensemble_accuracy = accuracy_score(y_test, ensemble_pred)
            training_results['ensemble'] = {'accuracy': ensemble_accuracy}
            logger.info(f"Ensemble accuracy: {ensemble_accuracy:.4f}")
        
        self.performance_metrics = training_results
        
        # Save models
        self._save_models()
        
        return training_results
    
    def _ensemble_predict(self, X_scaled: np.ndarray, X_original: np.ndarray) -> np.ndarray:
        """Make ensemble predictions using weighted voting."""
        predictions = []
        weights = []
        
        for model_name, model in self.models.items():
            try:
                # Use appropriate data format for each model
                if model_name == 'lightgbm':
                    pred_proba = model.predict_proba(X_scaled)
                else:
                    pred_proba = model.predict_proba(X_original)
                
                predictions.append(pred_proba)
                weights.append(self.model_weights.get(model_name, 0.25))
                
            except Exception as e:
                logger.warning(f"Error in ensemble prediction for {model_name}: {e}")
                continue
        
        if not predictions:
            raise ValueError("No models available for ensemble prediction")
        
        # Weighted average of probabilities
        weighted_proba = np.average(predictions, axis=0, weights=weights)
        
        # Return class with highest probability
        return np.argmax(weighted_proba, axis=1)
    
    def predict_with_confidence(self, symptoms: List[str], 
                              user_profile: Dict[str, Any] = None) -> List[PredictionResult]:
        """
        Make predictions with confidence scores and detailed analysis.
        
        Args:
            symptoms: List of symptom strings
            user_profile: Optional user profile for personalized predictions
            
        Returns:
            List of PredictionResult objects
        """
        if not self.models:
            logger.warning("No trained models available, using fallback predictions")
            return self._fallback_predictions(symptoms)
        
        try:
            # Preprocess symptoms
            processed_symptoms = self._preprocess_symptoms(symptoms)
            
            # Feature engineering
            features = self._extract_features(processed_symptoms, user_profile)
            
            # Make ensemble predictions
            predictions = []
            confidence_scores = []
            
            for model_name, model in self.models.items():
                try:
                    # Use appropriate data format
                    if model_name == 'lightgbm':
                        X = self.scalers['standard'].transform([features])
                    else:
                        X = np.array([features])
                    
                    pred_proba = model.predict_proba(X)[0]
                    pred_classes = model.classes_
                    
                    # Store top predictions
                    top_indices = np.argsort(pred_proba)[::-1][:5]
                    for idx in top_indices:
                        disease = pred_classes[idx]
                        probability = pred_proba[idx]
                        
                        predictions.append((disease, probability, model_name))
                        
                except Exception as e:
                    logger.warning(f"Error in prediction for {model_name}: {e}")
                    continue
            
            # Aggregate predictions
            aggregated_predictions = self._aggregate_predictions(predictions)
            
            # Generate detailed results
            results = []
            for disease, probability in aggregated_predictions[:5]:
                confidence = self._calculate_confidence(probability)
                risk_level = self._assess_risk_level(disease, processed_symptoms)
                recommendations = self._get_recommendations(disease, processed_symptoms)
                follow_up = self._get_follow_up_questions(disease, processed_symptoms)
                
                results.append(PredictionResult(
                    disease=disease,
                    probability=probability,
                    confidence=confidence,
                    risk_level=risk_level,
                    recommendations=recommendations,
                    follow_up=follow_up
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in prediction: {e}")
            return self._fallback_predictions(symptoms)
    
    def analyze_symptoms(self, symptoms: List[str], 
                        user_profile: Dict[str, Any] = None) -> SymptomAnalysis:
        """
        Perform comprehensive symptom analysis.
        
        Args:
            symptoms: List of symptom strings
            user_profile: Optional user profile
            
        Returns:
            SymptomAnalysis object with detailed analysis
        """
        processed_symptoms = self._preprocess_symptoms(symptoms)
        
        # Calculate severity
        severity_score, severity_level = self._calculate_severity(processed_symptoms)
        
        # Check for emergency
        emergency_flag = self.emergency_detector.is_emergency(processed_symptoms, severity_score)
        
        # Identify affected body systems
        body_systems = self._identify_body_systems(processed_symptoms)
        
        # Analyze symptom patterns
        patterns = self._analyze_symptom_patterns(processed_symptoms)
        
        return SymptomAnalysis(
            symptoms=processed_symptoms,
            severity_score=severity_score,
            severity_level=severity_level,
            emergency_flag=emergency_flag,
            body_systems_affected=body_systems,
            symptom_patterns=patterns
        )
    
    def _preprocess_symptoms(self, symptoms: List[str]) -> List[str]:
        """Preprocess and normalize symptom strings."""
        processed = []
        for symptom in symptoms:
            # Normalize case and spacing
            normalized = symptom.lower().strip().replace(' ', '_')
            
            # Apply medical synonym mapping
            normalized = self._apply_medical_synonyms(normalized)
            
            processed.append(normalized)
        
        return list(set(processed))  # Remove duplicates
    
    def _apply_medical_synonyms(self, symptom: str) -> str:
        """Apply medical synonym mapping."""
        synonym_map = {
            'stomach_ache': 'abdominal_pain',
            'belly_pain': 'abdominal_pain',
            'tummy_pain': 'abdominal_pain',
            'throwing_up': 'vomiting',
            'feeling_sick': 'nausea',
            'can_not_sleep': 'insomnia',
            'trouble_sleeping': 'insomnia',
            'feeling_tired': 'fatigue',
            'no_energy': 'fatigue',
            'high_temperature': 'fever',
            'runny_nose': 'nasal_discharge',
            'stuffy_nose': 'nasal_congestion'
        }
        
        return synonym_map.get(symptom, symptom)
    
    def _extract_features(self, symptoms: List[str], 
                         user_profile: Dict[str, Any] = None) -> List[float]:
        """Extract features for ML models."""
        features = []
        
        # Binary symptom features
        if hasattr(self, 'feature_names'):
            for feature_name in self.feature_names:
                features.append(1.0 if feature_name in symptoms else 0.0)
        else:
            # Fallback: create features based on known symptoms
            known_symptoms = list(self.symptom_knowledge.keys())
            for symptom in known_symptoms:
                features.append(1.0 if symptom in symptoms else 0.0)
        
        # Additional engineered features
        features.extend([
            len(symptoms),  # Number of symptoms
            self._calculate_severity(symptoms)[0],  # Severity score
            len(self._identify_body_systems(symptoms)),  # Number of body systems
        ])
        
        # User profile features (if available)
        if user_profile:
            features.extend([
                user_profile.get('age', 30) / 100.0,  # Normalized age
                1.0 if user_profile.get('gender') == 'female' else 0.0,
                len(user_profile.get('medical_history', [])) / 10.0,  # Medical history complexity
            ])
        else:
            features.extend([0.3, 0.5, 0.0])  # Default values
        
        return features
    
    def _calculate_severity(self, symptoms: List[str]) -> Tuple[float, str]:
        """Calculate symptom severity score and level."""
        total_weight = 0
        max_weight = 0
        
        for symptom in symptoms:
            weight = self.symptom_knowledge.get(symptom, {}).get('severity_weight', 3)
            total_weight += weight
            max_weight = max(max_weight, weight)
        
        if not symptoms:
            return 0.0, "Unknown"
        
        # Combine average and maximum weights
        avg_severity = total_weight / len(symptoms)
        severity_score = (avg_severity + max_weight) / 2
        
        # Determine level
        if severity_score < 3:
            level = "Low"
        elif severity_score < 6:
            level = "Moderate"
        elif severity_score < 8:
            level = "High"
        else:
            level = "Critical"
        
        return severity_score, level
    
    def _identify_body_systems(self, symptoms: List[str]) -> List[str]:
        """Identify affected body systems."""
        systems = set()
        
        for symptom in symptoms:
            system = self.symptom_knowledge.get(symptom, {}).get('body_system')
            if system:
                systems.add(system)
        
        return list(systems)
    
    def _analyze_symptom_patterns(self, symptoms: List[str]) -> Dict[str, Any]:
        """Analyze patterns in symptoms."""
        patterns = {
            'symptom_count': len(symptoms),
            'emergency_symptoms': [],
            'chronic_indicators': [],
            'acute_indicators': [],
            'system_clusters': {}
        }
        
        # Identify emergency symptoms
        for symptom in symptoms:
            if self.symptom_knowledge.get(symptom, {}).get('severity_weight', 0) >= 8:
                patterns['emergency_symptoms'].append(symptom)
        
        # Group by body systems
        for symptom in symptoms:
            system = self.symptom_knowledge.get(symptom, {}).get('body_system', 'other')
            if system not in patterns['system_clusters']:
                patterns['system_clusters'][system] = []
            patterns['system_clusters'][system].append(symptom)
        
        return patterns
    
    def _aggregate_predictions(self, predictions: List[Tuple[str, float, str]]) -> List[Tuple[str, float]]:
        """Aggregate predictions from multiple models."""
        disease_scores = {}
        disease_counts = {}
        
        for disease, probability, model_name in predictions:
            weight = self.model_weights.get(model_name, 0.25)
            
            if disease not in disease_scores:
                disease_scores[disease] = 0
                disease_counts[disease] = 0
            
            disease_scores[disease] += probability * weight
            disease_counts[disease] += weight
        
        # Calculate weighted averages
        aggregated = []
        for disease, total_score in disease_scores.items():
            avg_score = total_score / disease_counts[disease]
            aggregated.append((disease, avg_score))
        
        # Sort by probability
        aggregated.sort(key=lambda x: x[1], reverse=True)
        
        return aggregated
    
    def _calculate_confidence(self, probability: float) -> str:
        """Calculate confidence level from probability."""
        if probability >= 0.8:
            return "Very High"
        elif probability >= 0.6:
            return "High"
        elif probability >= 0.4:
            return "Medium"
        elif probability >= 0.2:
            return "Low"
        else:
            return "Very Low"
    
    def _assess_risk_level(self, disease: str, symptoms: List[str]) -> str:
        """Assess risk level for a disease."""
        disease_info = self.disease_knowledge.get(disease, {})
        base_severity = disease_info.get('severity', 'moderate')
        
        # Adjust based on symptoms
        severity_score = self._calculate_severity(symptoms)[0]
        
        if severity_score >= 8 or base_severity == 'critical':
            return "Critical"
        elif severity_score >= 6 or base_severity == 'severe':
            return "High"
        elif severity_score >= 4 or base_severity == 'moderate':
            return "Medium"
        else:
            return "Low"
    
    def _get_recommendations(self, disease: str, symptoms: List[str]) -> List[str]:
        """Get recommendations for a disease."""
        disease_info = self.disease_knowledge.get(disease, {})
        recommendations = disease_info.get('recommendations', [])
        
        if not recommendations:
            # Default recommendations based on severity
            severity_score = self._calculate_severity(symptoms)[0]
            if severity_score >= 8:
                recommendations = [
                    "Seek immediate medical attention",
                    "Do not delay treatment",
                    "Consider emergency room visit"
                ]
            elif severity_score >= 6:
                recommendations = [
                    "Schedule urgent doctor appointment",
                    "Monitor symptoms closely",
                    "Rest and stay hydrated"
                ]
            else:
                recommendations = [
                    "Schedule routine doctor appointment",
                    "Rest and maintain good nutrition",
                    "Monitor symptom progression"
                ]
        
        return recommendations
    
    def _get_follow_up_questions(self, disease: str, symptoms: List[str]) -> List[str]:
        """Get follow-up questions for a disease."""
        questions = [
            "How long have you been experiencing these symptoms?",
            "Have the symptoms been getting better or worse?",
            "Are you currently taking any medications?"
        ]
        
        # Disease-specific questions
        disease_questions = {
            'common_cold': [
                "Have you been in contact with others who are sick?",
                "Do you have a fever?"
            ],
            'influenza': [
                "Did the symptoms come on suddenly?",
                "Have you had your flu vaccination this year?"
            ],
            'migraine': [
                "Do you have sensitivity to light or sound?",
                "Do you have a family history of migraines?"
            ]
        }
        
        specific_questions = disease_questions.get(disease, [])
        questions.extend(specific_questions)
        
        return questions[:5]  # Limit to 5 questions
    
    def _fallback_predictions(self, symptoms: List[str]) -> List[PredictionResult]:
        """Provide fallback predictions when models are not available."""
        # Simple rule-based predictions
        fallback_diseases = {
            'common_cold': 0.7,
            'influenza': 0.6,
            'allergic_reaction': 0.5,
            'viral_infection': 0.4,
            'bacterial_infection': 0.3
        }
        
        results = []
        for disease, probability in fallback_diseases.items():
            results.append(PredictionResult(
                disease=disease,
                probability=probability,
                confidence=self._calculate_confidence(probability),
                risk_level="Medium",
                recommendations=["Consult with healthcare provider"],
                follow_up=["Monitor symptoms", "Stay hydrated"]
            ))
        
        return results
    
    def _save_models(self):
        """Save trained models and encoders."""
        try:
            models_dir = 'models'
            os.makedirs(models_dir, exist_ok=True)
            
            # Save individual models
            for model_name, model in self.models.items():
                model_path = os.path.join(models_dir, f'{model_name}_model.pkl')
                joblib.dump(model, model_path)
            
            # Save encoders and scalers
            encoders_path = os.path.join(models_dir, 'encoders.pkl')
            joblib.dump({
                'scalers': self.scalers,
                'label_encoder': getattr(self, 'label_encoder', None),
                'feature_names': getattr(self, 'feature_names', [])
            }, encoders_path)
            
            # Save performance metrics
            metrics_path = os.path.join(models_dir, 'performance_metrics.json')
            with open(metrics_path, 'w') as f:
                json.dump(self.performance_metrics, f, indent=2)
            
            logger.info("Models saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def load_models(self):
        """Load trained models and encoders."""
        try:
            models_dir = 'models'
            
            # Load individual models
            for model_name in self.model_weights.keys():
                model_path = os.path.join(models_dir, f'{model_name}_model.pkl')
                if os.path.exists(model_path):
                    self.models[model_name] = joblib.load(model_path)
            
            # Load encoders and scalers
            encoders_path = os.path.join(models_dir, 'encoders.pkl')
            if os.path.exists(encoders_path):
                encoders_data = joblib.load(encoders_path)
                self.scalers = encoders_data.get('scalers', {})
                self.label_encoder = encoders_data.get('label_encoder')
                self.feature_names = encoders_data.get('feature_names', [])
            
            # Load performance metrics
            metrics_path = os.path.join(models_dir, 'performance_metrics.json')
            if os.path.exists(metrics_path):
                with open(metrics_path, 'r') as f:
                    self.performance_metrics = json.load(f)
            
            logger.info(f"Loaded {len(self.models)} models successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")

class EmergencyDetector:
    """Specialized class for detecting medical emergencies."""
    
    def __init__(self):
        self.emergency_symptoms = {
            'chest_pain': 9,
            'severe_chest_pain': 10,
            'shortness_of_breath': 8,
            'difficulty_breathing': 9,
            'sudden_numbness': 9,
            'sudden_weakness': 9,
            'facial_drooping': 10,
            'slurred_speech': 9,
            'severe_headache': 8,
            'loss_of_consciousness': 10,
            'seizure': 10,
            'severe_bleeding': 10,
            'coughing_blood': 9,
            'vomiting_blood': 9,
            'severe_abdominal_pain': 8,
            'sudden_vision_loss': 9,
            'paralysis': 10
        }
        
        self.emergency_combinations = [
            ['chest_pain', 'shortness_of_breath'],
            ['headache', 'stiff_neck', 'fever'],
            ['severe_abdominal_pain', 'vomiting'],
            ['confusion', 'fever', 'headache']
        ]
    
    def is_emergency(self, symptoms: List[str], severity_score: float = 0) -> bool:
        """
        Determine if symptoms indicate a medical emergency.
        
        Args:
            symptoms: List of symptom strings
            severity_score: Overall severity score
            
        Returns:
            Boolean indicating emergency status
        """
        # Check individual emergency symptoms
        for symptom in symptoms:
            if symptom in self.emergency_symptoms:
                if self.emergency_symptoms[symptom] >= 9:
                    return True
        
        # Check emergency combinations
        for combination in self.emergency_combinations:
            if all(symptom in symptoms for symptom in combination):
                return True
        
        # Check severity threshold
        if severity_score >= 8.5:
            return True
        
        return False
    
    def get_emergency_message(self, symptoms: List[str]) -> str:
        """Get appropriate emergency message."""
        critical_symptoms = [s for s in symptoms if s in self.emergency_symptoms]
        
        if critical_symptoms:
            return (
                "⚠️ MEDICAL EMERGENCY: Your symptoms may indicate a serious medical condition "
                "that requires immediate attention. Please call emergency services (911) or "
                "go to the nearest emergency room immediately. Do not delay seeking medical care."
            )
        else:
            return (
                "⚠️ URGENT MEDICAL ATTENTION NEEDED: Your symptoms suggest you should seek "
                "immediate medical care. Please contact your doctor or go to an urgent care "
                "facility as soon as possible."
            )
