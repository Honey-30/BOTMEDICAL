"""
NLP Preprocessing Module for Symptom Checker

This module handles text preprocessing for symptom input,
including tokenization, spelling correction, and mapping to standard symptom terms.
"""

import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from difflib import get_close_matches

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

class SymptomPreprocessor:
    """
    A class for preprocessing symptom text input from users.
    """
    
    def __init__(self):
        """Initialize preprocessor with lemmatizer, stopwords, and symptom mappings."""
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Common symptom synonyms mapping
        self.symptom_synonyms = {
            "stomach ache": "abdominal pain",
            "tummy pain": "abdominal pain",
            "belly pain": "abdominal pain",
            "throwing up": "vomiting",
            "puke": "vomiting",
            "throw up": "vomiting",
            "dizzy": "dizziness",
            "feeling dizzy": "dizziness",
            "tired": "fatigue",
            "exhausted": "fatigue",
            "no energy": "fatigue",
            "can't sleep": "insomnia",
            "trouble sleeping": "insomnia",
            "sleeplessness": "insomnia",
            "fever": "high fever",
            "high temperature": "high fever",
            "cough": "continuous cough",
            "runny nose": "running nose",
            "stuffy nose": "congestion",
            "blocked nose": "congestion",
            "weak": "weakness",
            "muscle pain": "muscle ache",
            "body aches": "body pain",
            "shaking": "shivering",
            "irregular heartbeat": "palpitations",
            "rash": "skin rash",
            "can't breathe": "shortness of breath",
            "hard to breathe": "breathing difficulty",
            "breathing problem": "breathing difficulty",
            "headache": "headache",
            "head hurts": "headache",
            "migraine": "severe headache",
            "chest pain": "chest pain",
            "chest discomfort": "chest pain",
            "heart pain": "chest pain",
            "sore throat": "sore throat",
            "throat pain": "sore throat",
            "diarrhea": "diarrhoea",
            "loose stool": "diarrhoea",
            "constipation": "constipation",
            "can't poop": "constipation",
            "joint pain": "joint pain",
            "achy joints": "joint pain"
        }
        
        # Load standard symptom vocabulary from the model's symptom list if available
        self.standard_symptoms = []
        try:
            import os
            import pandas as pd
            
            # Try to load from dataset
            data_path = os.path.join('data', 'disease_symptom_dataset.csv')
            if os.path.exists(data_path):
                df = pd.read_csv(data_path)
                symptom_columns = [col for col in df.columns if 'Symptom' in col]
                
                # Extract all symptoms
                all_symptoms = []
                for col in symptom_columns:
                    all_symptoms.extend(df[col].dropna().unique())
                
                # Unique symptoms
                self.standard_symptoms = list(set([s for s in all_symptoms if isinstance(s, str) and s.strip() != '']))
                
        except Exception as e:
            print(f"Could not load standard symptoms: {e}")
            
            # Default set of common symptoms if loading fails
            self.standard_symptoms = [
                "abdominal pain", "high fever", "vomiting", "headache", "cough",
                "fatigue", "weakness", "chest pain", "back pain", "joint pain",
                "dizziness", "diarrhoea", "nausea", "muscle pain", "skin rash",
                "congestion", "sore throat", "shortness of breath", "runny nose",
                "chills", "insomnia", "anxiety", "depression", "eye pain", "ear pain"
            ]
    
    def preprocess_text(self, text):
        """
        Preprocess symptom text by cleaning, tokenizing, and lemmatizing.
        
        Args:
            text: String containing user's symptom description
            
        Returns:
            Preprocessed text with standardized tokens
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and lemmatize
        tokens = [self.lemmatizer.lemmatize(word) for word in tokens if word not in self.stop_words]
        
        # Join tokens back to text
        return " ".join(tokens)
    
    def extract_symptoms(self, text):
        """
        Extract and standardize symptoms from user input.
        
        Args:
            text: Preprocessed text containing symptom description
            
        Returns:
            List of standardized symptoms found in the text
        """
        # First preprocess the text
        text = self.preprocess_text(text)
        
        found_symptoms = []
        
        # Check for direct symptom mentions (multi-word symptoms first)
        for symptom in sorted(self.standard_symptoms, key=len, reverse=True):
            symptom_lower = symptom.lower()
            if symptom_lower in text:
                found_symptoms.append(symptom)
                # Remove the found symptom to avoid double counting
                text = text.replace(symptom_lower, "")
        
        # Check for symptom synonyms
        for synonym, standard in self.symptom_synonyms.items():
            if synonym in text and standard not in found_symptoms:
                found_symptoms.append(standard)
                # Remove the found synonym to avoid double counting
                text = text.replace(synonym, "")
        
        # If no symptoms found directly, try fuzzy matching with remaining words
        if not found_symptoms:
            words = text.split()
            for word in words:
                if len(word) > 3:  # Only consider words longer than 3 chars
                    matches = get_close_matches(word, self.standard_symptoms, n=1, cutoff=0.7)
                    if matches:
                        found_symptoms.append(matches[0])
        
        return list(set(found_symptoms))  # Remove duplicates
    
    def get_all_standard_symptoms(self):
        """
        Get the list of all standard symptoms for UI autocomplete.
        
        Returns:
            List of all standard symptoms in the vocabulary
        """
        return sorted(self.standard_symptoms)