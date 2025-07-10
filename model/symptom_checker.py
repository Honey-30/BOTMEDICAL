"""
Symptom Checker - Core Model Logic

This module contains the main ML model for symptom prediction
and the logic to match user symptoms to potential conditions.
"""

import numpy as np
import pandas as pd
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MultiLabelBinarizer

class SymptomChecker:
    """
    A class that implements symptom checking and disease prediction.
    
    Attributes:
        model: The trained machine learning model
        symptom_encoder: Encoder for converting symptom names to indices
        disease_encoder: Encoder for converting disease indices to names
        symptom_severity: Dictionary mapping symptoms to their severity level
        remedies_data: Dictionary mapping diseases to remedies
    """
    
    def __init__(self):
        """Initialize the symptom checker with trained model and encoders."""
        self.model = None
        self.symptom_encoder = None
        self.disease_encoder = None
        self.symptom_severity = {}
        self.symptom_description = {}
        self.disease_description = {}
        self.symptom_precaution = {}
        self.remedies_data = {}
        
        # Load pre-trained model and encoders if they exist
        model_path = os.path.join('models', 'symptom_model.pkl')
        if os.path.exists(model_path):
            self.load_model(model_path)
        
        # Load severity and remedies data
        self._load_data()
    
    def _load_data(self):
        """Load symptom severity, descriptions, and remedies data from CSV files."""
        try:
            # Load severity data
            severity_path = os.path.join('data', 'symptom_severity.csv')
            if os.path.exists(severity_path):
                severity_df = pd.read_csv(severity_path)
                self.symptom_severity = dict(zip(severity_df['Symptom'], severity_df['weight']))
            
            # Load remedies data
            remedies_path = os.path.join('data', 'remedies_dataset.csv')
            if os.path.exists(remedies_path):
                remedies_df = pd.read_csv(remedies_path)
                # Group by disease
                for disease, group in remedies_df.groupby('Disease'):
                    self.remedies_data[disease] = group['Remedy'].tolist()
            
            # Load disease descriptions if available
            disease_desc_path = os.path.join('data', 'disease_description.csv')
            if os.path.exists(disease_desc_path):
                disease_df = pd.read_csv(disease_desc_path)
                self.disease_description = dict(zip(disease_df['Disease'], disease_df['Description']))
                
            # Load precautions if available
            precaution_path = os.path.join('data', 'symptom_precaution.csv')
            if os.path.exists(precaution_path):
                prec_df = pd.read_csv(precaution_path)
                # Group by disease and collect all precautions
                self.symptom_precaution = prec_df.groupby('Disease')['Precaution'].apply(list).to_dict()
                
        except Exception as e:
            print(f"Warning: Could not load data: {e}")
    
    def load_model(self, model_path):
        """Load the trained model and encoders from a pickle file."""
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.symptom_encoder = model_data['symptom_encoder']
            self.disease_encoder = model_data['disease_encoder']
            print("Model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
    
    def save_model(self, model_path):
        """Save the trained model and encoders to a pickle file."""
        if self.model is None:
            print("No model to save")
            return
            
        model_data = {
            'model': self.model,
            'symptom_encoder': self.symptom_encoder,
            'disease_encoder': self.disease_encoder
        }
        
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"Model saved to {model_path}")
    
    def train(self, symptoms_data, diseases):
        """
        Train the symptom checker model.
        
        Args:
            symptoms_data: List of lists, where each inner list contains symptoms for one case
            diseases: List of disease labels corresponding to each symptom list
        """
        # Create MultiLabelBinarizer for symptoms
        self.symptom_encoder = MultiLabelBinarizer()
        X = self.symptom_encoder.fit_transform(symptoms_data)
        
        # Train a random forest classifier
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X, diseases)
        
        # Store disease labels
        self.disease_encoder = {i: disease for i, disease in enumerate(self.model.classes_)}
        
        print(f"Model trained on {len(symptoms_data)} samples with {len(self.symptom_encoder.classes_)} unique symptoms")
    
    def predict(self, symptoms):
        """
        Predict potential diseases based on a list of symptoms.
        
        Args:
            symptoms: List of symptom strings reported by the user
            
        Returns:
            List of tuples (disease, probability) sorted by probability
        """
        if self.model is None:
            # Fallback for demo when model isn't loaded
            import random
            fallback_diseases = ["Common Cold", "Influenza", "Allergic Rhinitis", "Migraine", "Gastroenteritis"]
            return [(disease, random.uniform(0.3, 0.9)) for disease in fallback_diseases[:3]]
        
        # Transform symptoms into the format expected by the model
        X = self.symptom_encoder.transform([symptoms])
        
        # Get prediction probabilities for all classes
        probabilities = self.model.predict_proba(X)[0]
        
        # Sort by probability (descending) and return top results
        results = [(self.disease_encoder[i], prob) for i, prob in enumerate(probabilities)]
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top 5 predictions or all if less than 5
        return results[:5]
    
    def calculate_severity(self, symptoms):
        """
        Calculate the overall severity score based on reported symptoms.
        
        Args:
            symptoms: List of symptom strings
            
        Returns:
            Tuple of (severity_score, severity_level) where severity_level is a string
        """
        if not symptoms:
            return 0, "Unknown"
            
        # Calculate total severity
        total_severity = sum(self.symptom_severity.get(symptom, 1) for symptom in symptoms)
        avg_severity = total_severity / len(symptoms)
        
        # Determine severity level
        if avg_severity < 3:
            severity_level = "Low"
        elif avg_severity < 6:
            severity_level = "Moderate"
        else:
            severity_level = "High"
            
        return avg_severity, severity_level
    
    def get_emergency_symptoms(self):
        """Return a list of symptoms that are considered medical emergencies."""
        emergency_symptoms = [
            "chest pain", "severe chest pain", "shortness of breath", "difficulty breathing",
            "sudden numbness", "sudden weakness", "paralysis", "facial drooping", 
            "slurred speech", "severe headache", "sudden severe headache", "loss of consciousness",
            "unresponsiveness", "seizure", "severe bleeding", "coughing up blood"
        ]
        return emergency_symptoms
    
    def is_emergency(self, symptoms):
        """
        Check if the symptoms indicate a potential medical emergency.
        
        Args:
            symptoms: List of symptom strings
            
        Returns:
            Boolean indicating if emergency medical attention may be needed
        """
        emergency_symptoms = self.get_emergency_symptoms()
        
        # Check if any symptoms match emergency symptoms
        for symptom in symptoms:
            if any(e_symptom in symptom.lower() for e_symptom in emergency_symptoms):
                return True
                
        # Also check severity
        severity_score, _ = self.calculate_severity(symptoms)
        if severity_score > 7:  # High severity threshold
            return True
            
        return False
    
    def get_precautions(self, disease):
        """Get precautions for a specific disease if available."""
        return self.symptom_precaution.get(disease, 
                ["Consult with a healthcare professional for proper diagnosis and treatment"])
    
    def get_symptom_info(self, symptom):
        """Get information about a specific symptom if available."""
        return self.symptom_description.get(symptom, "No detailed information available.")
    
    def get_disease_info(self, disease):
        """Get information about a specific disease if available."""
        return self.disease_description.get(disease, 
            f"{disease} is a medical condition that should be properly diagnosed by a healthcare professional.")
    
    def get_remedies(self, disease):
        """
        Get remedies for a specific disease if available.
        
        Args:
            disease: String name of the disease
            
        Returns:
            List of remedies for the disease
        """
        default_remedies = [
            "Consult with a healthcare professional for proper treatment",
            "Rest and ensure adequate hydration",
            "Follow a balanced diet",
            "Avoid self-medication without professional guidance"
        ]
        
        return self.remedies_data.get(disease, default_remedies)