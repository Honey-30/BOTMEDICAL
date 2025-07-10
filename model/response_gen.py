"""
Response Generator Module

This module generates appropriate responses based on symptom analysis,
prediction results, and remedies from the symptom checker.
"""

class ResponseGenerator:
    """
    A class for generating appropriate responses to user symptom inputs.
    """
    
    def __init__(self):
        """Initialize response generator with template responses."""
        # Template responses for different scenarios
        self.templates = {
            'greeting': [
                "Hello! I'm your AI health assistant. How can I help you today?",
                "Welcome to the AI Health Checker. What symptoms are you experiencing?",
                "Hi there! I'm here to help identify potential health concerns. Please describe your symptoms."
            ],
            
            'prompt': [
                "Could you please describe any symptoms you're experiencing?",
                "What symptoms have you been feeling lately?",
                "Please tell me about any health issues you're currently experiencing."
            ],
            
            'clarify': [
                "Could you provide more details about your {}?",
                "When did your {} start? Any other symptoms along with it?",
                "Can you describe your {} in more detail? Is it constant or intermittent?"
            ],
            
            'emergency': [
                "⚠️ IMPORTANT: The symptoms you've described may require immediate medical attention. Please contact emergency services or go to the nearest emergency room.",
                "⚠️ WARNING: Your symptoms suggest a potentially serious condition. Please seek immediate medical care.",
                "⚠️ URGENT: Based on what you've told me, you should seek emergency medical care right away."
            ],
            
            'disclaimer': [
                "Please remember that this is an AI assistant and not a replacement for professional medical advice. Always consult with a healthcare provider for proper diagnosis and treatment.",
                "Note: This AI provides general information only and is not a substitute for professional medical advice or diagnosis.",
                "Remember: While I can help identify potential conditions, only a qualified healthcare professional can provide a proper diagnosis."
            ],
            
            'no_symptoms': [
                "I couldn't identify any specific symptoms from what you've described. Could you please be more specific about how you're feeling?",
                "I need more information to help you. Could you describe your symptoms in more detail?",
                "I'm not sure I understood your symptoms correctly. Could you rephrase or provide more details?"
            ],
            
            'low_confidence': [
                "Based on the limited information provided, it's difficult to determine a specific condition. Consider consulting a healthcare professional.",
                "The symptoms you've described could be related to multiple conditions. A healthcare provider would be better able to assess your situation.",
                "I don't have enough information to make a confident assessment. Please consider discussing your symptoms with a doctor."
            ],
        }
    
    def get_greeting(self):
        """Return a random greeting message."""
        import random
        return random.choice(self.templates['greeting'])
    
    def get_prompt(self):
        """Return a random prompt for symptoms."""
        import random
        return random.choice(self.templates['prompt'])
    
    def get_clarification(self, symptom):
        """Get a clarification question for a specific symptom."""
        import random
        template = random.choice(self.templates['clarify'])
        return template.format(symptom)
    
    def get_emergency_message(self):
        """Return an emergency warning message."""
        import random
        return random.choice(self.templates['emergency'])
    
    def get_disclaimer(self):
        """Return a medical disclaimer."""
        import random
        return random.choice(self.templates['disclaimer'])
    
    def generate_prediction_response(self, predictions, symptoms, is_emergency, severity, remedies=None):
        """
        Generate a response based on predictions, symptom analysis and remedies.
        
        Args:
            predictions: List of (disease, probability) tuples
            symptoms: List of identified symptoms
            is_emergency: Boolean indicating if symptoms suggest an emergency
            severity: Tuple of (severity_score, severity_level)
            remedies: Dictionary mapping diseases to remedy lists
            
        Returns:
            Formatted response string
        """
        import random
        
        # Check if emergency
        if is_emergency:
            return self.get_emergency_message()
        
        # If no symptoms were identified
        if not symptoms:
            return random.choice(self.templates['no_symptoms'])
        
        # If predictions have low confidence (highest probability < 0.4)
        if not predictions or predictions[0][1] < 0.4:
            return random.choice(self.templates['low_confidence'])
        
        # Format the symptoms
        symptom_text = ", ".join(symptoms[:-1]) + (" and " + symptoms[-1] if len(symptoms) > 1 else symptoms[0])
        
        # Format the prediction results
        response = f"Based on your reported symptoms ({symptom_text}), here are potential conditions:\n\n"
        
        for disease, probability in predictions[:3]:  # Show top 3
            confidence = "High" if probability > 0.7 else "Medium" if probability > 0.5 else "Low"
            prob_percent = int(probability * 100)
            response += f"• {disease} - {confidence} confidence ({prob_percent}%)\n"
        
        response += f"\nOverall severity: {severity[1]} ({severity[0]:.1f}/10)\n\n"
        
        # Add remedies for the top condition if available
        if remedies and predictions:
            top_disease = predictions[0][0]
            if top_disease in remedies:
                response += f"Suggested remedies for {top_disease}:\n"
                for remedy in remedies[top_disease][:3]:  # Show top 3 remedies
                    response += f"✓ {remedy}\n"
                response += "\n"
        
        # Add a disclaimer
        response += self.get_disclaimer()
        
        return response
    
    def generate_followup_questions(self, top_disease, symptoms):
        """
        Generate follow-up questions based on the top predicted disease.
        
        Args:
            top_disease: The most likely disease predicted
            symptoms: List of symptoms already reported
            
        Returns:
            List of follow-up questions
        """
        # Disease-specific follow-up questions
        disease_questions = {
            "Common Cold": [
                "How long have you had these symptoms?",
                "Are you experiencing any fever or chills?",
                "Have you been in contact with anyone who has similar symptoms?"
            ],
            "Influenza": [
                "How quickly did your symptoms come on?",
                "Are you experiencing body aches or unusual fatigue?",
                "Have you had your flu shot this year?"
            ],
            "Migraine": [
                "Do you experience sensitivity to light or sound?",
                "Do you have a history of migraines?",
                "Do you notice any warning signs before the headache begins?"
            ],
            "Hypertension": [
                "Do you have a history of high blood pressure?",
                "Are you currently taking any medication for blood pressure?",
                "Do you monitor your blood pressure at home?"
            ],
            "Diabetes": [
                "Have you noticed increased thirst or frequent urination?",
                "Is there a history of diabetes in your family?",
                "Have you had your blood sugar levels checked recently?"
            ],
            "Asthma": [
                "Do you have a history of asthma or breathing problems?",
                "What triggers your breathing difficulties?",
                "Have you used an inhaler or breathing treatment before?"
            ],
            "Allergic Rhinitis": [
                "Do your symptoms worsen in specific environments or seasons?",
                "Have you tried any antihistamines or allergy medications?",
                "Do you have a history of allergies?"
            ],
            "Gastroenteritis": [
                "When did your stomach symptoms begin?",
                "Have you consumed any potentially contaminated food recently?",
                "Are others around you experiencing similar symptoms?"
            ]
        }
        
        # General follow-up questions
        general_questions = [
            "Are you currently taking any medications?",
            "Have these symptoms occurred before?",
            "Have you noticed anything that makes your symptoms better or worse?",
            "How long have you been experiencing these symptoms?",
            "Is there a family history of similar conditions?"
        ]
        
        # Get disease-specific questions if available
        questions = disease_questions.get(top_disease, [])
        
        # Add general questions if we don't have enough
        if len(questions) < 2:
            questions.extend(general_questions)
        
        # Limit to 3 questions
        return questions[:3]