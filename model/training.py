"""
Model Training Script

This script loads symptom-disease datasets and trains the symptom checker model.
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from model.symptom_checker import SymptomChecker

def load_dataset():
    """
    Load and preprocess the symptom-disease dataset.
    
    Returns:
        Tuple of (symptoms_list, diseases_list)
    """
    # Get path to the data directory
    data_dir = os.path.join('data')
    dataset_path = os.path.join(data_dir, 'disease_symptom_dataset.csv')
    
    # Load the dataset
    df = pd.read_csv(dataset_path)
    
    # Extract symptom columns
    symptom_cols = [col for col in df.columns if 'Symptom' in col]
    
    # Extract symptoms for each row, removing NaN values
    symptoms_list = []
    for _, row in df.iterrows():
        symptoms = [str(s).lower() for s in row[symptom_cols] if pd.notna(s) and str(s).strip() != '']
        symptoms_list.append(symptoms)
    
    # Extract disease labels
    diseases_list = df['Disease'].values
    
    print(f"Loaded dataset with {len(symptoms_list)} samples")
    print(f"Example: {diseases_list[0]} with symptoms {symptoms_list[0]}")
    
    return symptoms_list, diseases_list

def train_model():
    """
    Train the symptom checker model and save it.
    
    Returns:
        Trained SymptomChecker instance
    """
    print("Loading dataset...")
    symptoms_list, diseases_list = load_dataset()
    
    # Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        symptoms_list, diseases_list, test_size=0.2, random_state=42
    )
    
    print("Training model...")
    checker = SymptomChecker()
    checker.train(X_train, y_train)
    
    # Evaluate model
    print("Evaluating model...")
    X_test_encoded = checker.symptom_encoder.transform(X_test)
    y_pred = checker.model.predict(X_test_encoded)
    
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save the trained model
    model_path = os.path.join('models', 'symptom_model.pkl')
    checker.save_model(model_path)
    
    return checker

if __name__ == "__main__":
    # Make sure the data and models directories exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    
    print("Starting model training...")
    checker = train_model()
    print("Training complete!")