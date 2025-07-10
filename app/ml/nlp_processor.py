"""
Advanced NLP Processor for Medical Text Analysis
"""

import re
import string
import json
import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.chunk import ne_chunk
from nltk.tag import pos_tag
import spacy
from textblob import TextBlob
from fuzzywuzzy import fuzz, process
from transformers import pipeline, AutoTokenizer
import torch
from sentence_transformers import SentenceTransformer
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
    nltk.data.find('averaged_perceptron_tagger')
    nltk.data.find('maxent_ne_chunker')
    nltk.data.find('words')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('maxent_ne_chunker', quiet=True)
    nltk.download('words', quiet=True)

@dataclass
class ExtractedSymptom:
    """Structured representation of an extracted symptom."""
    original_text: str
    normalized_text: str
    confidence: float
    severity_indicators: List[str]
    temporal_indicators: List[str]
    location_indicators: List[str]
    frequency_indicators: List[str]

@dataclass
class MedicalEntity:
    """Structured representation of a medical entity."""
    text: str
    label: str
    confidence: float
    start_pos: int
    end_pos: int

class AdvancedMedicalNLP:
    """
    Advanced NLP processor for medical text analysis with multiple extraction methods.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the advanced NLP processor."""
        self.config = config or {}
        
        # Initialize NLTK components
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Remove medical stop words that might be important
        medical_stop_words = {'pain', 'hurt', 'feel', 'feeling', 'have', 'had', 'get', 'getting'}
        self.stop_words = self.stop_words - medical_stop_words
        
        # Load spaCy model if available
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded successfully")
        except IOError:
            logger.warning("spaCy model not found, using NLTK only")
            self.nlp = None
        
        # Load advanced models if available
        self.use_transformers = self.config.get('use_transformers', True)
        if self.use_transformers:
            try:
                # Medical NER model
                self.medical_ner = pipeline(
                    "ner",
                    model="dmis-lab/biobert-base-cased-v1.2-ner",
                    aggregation_strategy="simple"
                )
                
                # Sentence transformer for semantic similarity
                self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
                
                # Medical question answering model
                self.medical_qa = pipeline(
                    "question-answering",
                    model="dmis-lab/biobert-base-cased-v1.2-squad"
                )
                
                logger.info("Advanced transformer models loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load transformer models: {e}")
                self.use_transformers = False
        
        # Load medical vocabulary and mappings
        self.symptom_vocabulary = self._load_symptom_vocabulary()
        self.symptom_synonyms = self._load_symptom_synonyms()
        self.severity_keywords = self._load_severity_keywords()
        self.temporal_keywords = self._load_temporal_keywords()
        self.location_keywords = self._load_location_keywords()
        self.frequency_keywords = self._load_frequency_keywords()
        
        # Medical regex patterns
        self.medical_patterns = self._compile_medical_patterns()
        
    def _load_symptom_vocabulary(self) -> Dict[str, Dict[str, Any]]:
        """Load comprehensive symptom vocabulary."""
        # This would typically be loaded from a medical database
        return {
            "pain": {
                "category": "sensation",
                "severity_modifiers": ["mild", "moderate", "severe", "excruciating"],
                "location_modifiers": ["abdominal", "chest", "head", "back", "joint"],
                "type_modifiers": ["sharp", "dull", "throbbing", "burning", "stabbing"]
            },
            "fever": {
                "category": "vital_sign",
                "severity_modifiers": ["low-grade", "high", "very high"],
                "synonyms": ["temperature", "pyrexia", "hyperthermia"]
            },
            "nausea": {
                "category": "gastrointestinal",
                "related_symptoms": ["vomiting", "dizziness", "stomach_upset"],
                "synonyms": ["feeling_sick", "queasy", "sick_to_stomach"]
            },
            "fatigue": {
                "category": "constitutional",
                "severity_modifiers": ["mild", "moderate", "severe", "extreme"],
                "synonyms": ["tiredness", "exhaustion", "weakness", "lethargy"]
            },
            "cough": {
                "category": "respiratory",
                "type_modifiers": ["dry", "wet", "productive", "persistent", "chronic"],
                "severity_modifiers": ["mild", "severe", "violent"]
            },
            "headache": {
                "category": "neurological",
                "type_modifiers": ["tension", "migraine", "cluster", "sinus"],
                "location_modifiers": ["frontal", "temporal", "occipital", "bilateral"]
            },
            "shortness_of_breath": {
                "category": "respiratory",
                "synonyms": ["dyspnea", "breathing_difficulty", "breathlessness"],
                "triggers": ["exertion", "rest", "lying_down"]
            },
            "dizziness": {
                "category": "neurological",
                "synonyms": ["vertigo", "lightheadedness", "unsteadiness"],
                "triggers": ["standing", "movement", "turning_head"]
            }
        }
    
    def _load_symptom_synonyms(self) -> Dict[str, str]:
        """Load symptom synonym mappings."""
        return {
            # Pain synonyms
            "ache": "pain",
            "hurt": "pain",
            "hurts": "pain",
            "hurting": "pain",
            "sore": "pain",
            "soreness": "pain",
            "discomfort": "pain",
            "tender": "pain",
            "tenderness": "pain",
            
            # Fever synonyms
            "temperature": "fever",
            "hot": "fever",
            "burning_up": "fever",
            "feverish": "fever",
            "pyrexia": "fever",
            
            # Nausea synonyms
            "sick": "nausea",
            "queasy": "nausea",
            "sick_to_stomach": "nausea",
            "feeling_sick": "nausea",
            "stomach_upset": "nausea",
            
            # Fatigue synonyms
            "tired": "fatigue",
            "exhausted": "fatigue",
            "worn_out": "fatigue",
            "drained": "fatigue",
            "weak": "fatigue",
            "weakness": "fatigue",
            "lethargy": "fatigue",
            "lethargic": "fatigue",
            
            # Breathing synonyms
            "can't_breathe": "shortness_of_breath",
            "hard_to_breathe": "shortness_of_breath",
            "breathing_problems": "shortness_of_breath",
            "breathless": "shortness_of_breath",
            "out_of_breath": "shortness_of_breath",
            "winded": "shortness_of_breath",
            
            # Digestive synonyms
            "throwing_up": "vomiting",
            "puking": "vomiting",
            "sick": "vomiting",
            "upset_stomach": "nausea",
            "stomach_bug": "gastroenteritis",
            "diarrhea": "diarrhea",
            "loose_stools": "diarrhea",
            "runny_stool": "diarrhea",
            
            # Neurological synonyms
            "dizzy": "dizziness",
            "lightheaded": "dizziness",
            "spinning": "vertigo",
            "room_spinning": "vertigo",
            
            # Sleep synonyms
            "can't_sleep": "insomnia",
            "trouble_sleeping": "insomnia",
            "sleepless": "insomnia",
            "restless": "insomnia",
            
            # Skin synonyms
            "rash": "skin_rash",
            "itchy": "itching",
            "scratch": "itching",
            "bumps": "skin_rash",
            "hives": "skin_rash"
        }
    
    def _load_severity_keywords(self) -> Dict[str, float]:
        """Load severity indicator keywords and their weights."""
        return {
            # Mild severity
            "mild": 2.0,
            "slight": 2.0,
            "minor": 2.0,
            "little": 2.0,
            "light": 2.0,
            
            # Moderate severity
            "moderate": 5.0,
            "noticeable": 4.0,
            "uncomfortable": 4.0,
            "bothersome": 4.0,
            
            # High severity
            "severe": 8.0,
            "intense": 8.0,
            "strong": 7.0,
            "bad": 6.0,
            "terrible": 8.0,
            "awful": 8.0,
            "horrible": 8.0,
            
            # Extreme severity
            "excruciating": 10.0,
            "unbearable": 10.0,
            "extreme": 9.0,
            "worst": 10.0,
            "agonizing": 10.0,
            "crushing": 9.0,
            "stabbing": 8.0,
            "burning": 7.0,
            "throbbing": 6.0
        }
    
    def _load_temporal_keywords(self) -> Dict[str, str]:
        """Load temporal indicator keywords."""
        return {
            # Acute/sudden
            "sudden": "acute",
            "suddenly": "acute",
            "abrupt": "acute",
            "immediate": "acute",
            "sharp": "acute",
            "quick": "acute",
            
            # Chronic/ongoing
            "chronic": "chronic",
            "ongoing": "chronic",
            "persistent": "chronic",
            "constant": "chronic",
            "continuous": "chronic",
            "always": "chronic",
            "daily": "chronic",
            
            # Intermittent
            "sometimes": "intermittent",
            "occasionally": "intermittent",
            "comes_and_goes": "intermittent",
            "on_and_off": "intermittent",
            "sporadic": "intermittent",
            
            # Progressive
            "getting_worse": "progressive",
            "worsening": "progressive",
            "increasing": "progressive",
            "spreading": "progressive"
        }
    
    def _load_location_keywords(self) -> Dict[str, str]:
        """Load anatomical location keywords."""
        return {
            # Head/Neck
            "head": "head",
            "skull": "head",
            "forehead": "head",
            "temple": "head",
            "neck": "neck",
            "throat": "throat",
            
            # Chest/Respiratory
            "chest": "chest",
            "breast": "chest",
            "lung": "chest",
            "heart": "chest",
            
            # Abdomen
            "stomach": "abdomen",
            "belly": "abdomen",
            "abdomen": "abdomen",
            "abdominal": "abdomen",
            "gut": "abdomen",
            
            # Back
            "back": "back",
            "spine": "back",
            "lower_back": "back",
            "upper_back": "back",
            
            # Extremities
            "arm": "extremity",
            "hand": "extremity",
            "leg": "extremity",
            "foot": "extremity",
            "joint": "joint",
            
            # General
            "all_over": "systemic",
            "everywhere": "systemic",
            "whole_body": "systemic"
        }
    
    def _load_frequency_keywords(self) -> Dict[str, str]:
        """Load frequency indicator keywords."""
        return {
            "constantly": "constant",
            "always": "constant",
            "continuous": "constant",
            "non-stop": "constant",
            
            "frequently": "frequent",
            "often": "frequent",
            "many_times": "frequent",
            "repeatedly": "frequent",
            
            "occasionally": "occasional",
            "sometimes": "occasional",
            "once_in_a_while": "occasional",
            
            "rarely": "rare",
            "seldom": "rare",
            "hardly_ever": "rare"
        }
    
    def _compile_medical_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regular expressions for medical pattern matching."""
        return {
            'pain_pattern': re.compile(
                r'\b(?:severe|mild|sharp|dull|burning|stabbing|throbbing|aching|crushing)?\s*'
                r'(?:pain|ache|hurt|discomfort|soreness)\s*'
                r'(?:in|at|on|around)?\s*'
                r'(?:my|the)?\s*'
                r'(?:head|chest|stomach|back|abdomen|throat|neck|arm|leg|joint|all_over)?',
                re.IGNORECASE
            ),
            'fever_pattern': re.compile(
                r'\b(?:high|low|mild)?\s*(?:fever|temperature|hot|burning_up|feverish)\b',
                re.IGNORECASE
            ),
            'duration_pattern': re.compile(
                r'\b(?:for|since|about|over|lasting)\s*'
                r'(?:the\s+past\s+|last\s+)?'
                r'(\d+)\s*(day|days|week|weeks|month|months|hour|hours|minute|minutes)s?\b',
                re.IGNORECASE
            ),
            'severity_pattern': re.compile(
                r'\b(mild|moderate|severe|extreme|unbearable|excruciating|terrible|awful|bad|horrible)\b',
                re.IGNORECASE
            ),
            'frequency_pattern': re.compile(
                r'\b(always|constantly|frequently|often|sometimes|occasionally|rarely|never)\b',
                re.IGNORECASE
            )
        }
    
    def extract_symptoms(self, text: str, 
                        context: Dict[str, Any] = None) -> List[ExtractedSymptom]:
        """
        Extract symptoms from text using multiple NLP techniques.
        
        Args:
            text: Input text describing symptoms
            context: Optional context information (user profile, chat history)
            
        Returns:
            List of ExtractedSymptom objects
        """
        # Preprocess text
        processed_text = self._preprocess_text(text)
        
        # Multiple extraction methods
        extracted_symptoms = []
        
        # Method 1: Rule-based extraction using patterns
        rule_based = self._extract_with_rules(processed_text)
        extracted_symptoms.extend(rule_based)
        
        # Method 2: Fuzzy matching against symptom vocabulary
        fuzzy_matched = self._extract_with_fuzzy_matching(processed_text)
        extracted_symptoms.extend(fuzzy_matched)
        
        # Method 3: NER using spaCy (if available)
        if self.nlp:
            spacy_extracted = self._extract_with_spacy(text)
            extracted_symptoms.extend(spacy_extracted)
        
        # Method 4: Transformer-based NER (if available)
        if self.use_transformers:
            transformer_extracted = self._extract_with_transformers(text)
            extracted_symptoms.extend(transformer_extracted)
        
        # Method 5: Semantic similarity matching
        semantic_matched = self._extract_with_semantics(processed_text)
        extracted_symptoms.extend(semantic_matched)
        
        # Consolidate and rank results
        consolidated = self._consolidate_symptoms(extracted_symptoms)
        
        # Filter by confidence threshold
        confidence_threshold = self.config.get('confidence_threshold', 0.3)
        filtered = [s for s in consolidated if s.confidence >= confidence_threshold]
        
        return filtered
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for symptom extraction."""
        # Convert to lowercase
        text = text.lower()
        
        # Handle contractions
        contractions = {
            "can't": "cannot",
            "won't": "will not",
            "don't": "do not",
            "i'm": "i am",
            "i've": "i have",
            "i'll": "i will"
        }
        
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
        
        # Normalize spacing
        text = re.sub(r'\s+', ' ', text)
        
        # Handle common medical abbreviations
        abbreviations = {
            "bp": "blood pressure",
            "hr": "heart rate",
            "temp": "temperature",
            "wt": "weight",
            "ht": "height"
        }
        
        for abbrev, full_form in abbreviations.items():
            text = re.sub(rf'\b{abbrev}\b', full_form, text)
        
        return text.strip()
    
    def _extract_with_rules(self, text: str) -> List[ExtractedSymptom]:
        """Extract symptoms using rule-based pattern matching."""
        extracted = []
        
        # Pain extraction
        pain_matches = self.medical_patterns['pain_pattern'].finditer(text)
        for match in pain_matches:
            symptom_text = match.group().strip()
            normalized = self._normalize_symptom(symptom_text)
            
            severity_indicators = self._extract_severity_indicators(symptom_text)
            location_indicators = self._extract_location_indicators(symptom_text)
            
            extracted.append(ExtractedSymptom(
                original_text=symptom_text,
                normalized_text=normalized,
                confidence=0.8,
                severity_indicators=severity_indicators,
                temporal_indicators=[],
                location_indicators=location_indicators,
                frequency_indicators=[]
            ))
        
        # Fever extraction
        fever_matches = self.medical_patterns['fever_pattern'].finditer(text)
        for match in fever_matches:
            symptom_text = match.group().strip()
            severity_indicators = self._extract_severity_indicators(symptom_text)
            
            extracted.append(ExtractedSymptom(
                original_text=symptom_text,
                normalized_text="fever",
                confidence=0.9,
                severity_indicators=severity_indicators,
                temporal_indicators=[],
                location_indicators=[],
                frequency_indicators=[]
            ))
        
        return extracted
    
    def _extract_with_fuzzy_matching(self, text: str) -> List[ExtractedSymptom]:
        """Extract symptoms using fuzzy string matching."""
        extracted = []
        
        # Tokenize text
        tokens = word_tokenize(text)
        
        # Generate n-grams (1-3 words)
        ngrams = []
        for i in range(len(tokens)):
            for j in range(i + 1, min(i + 4, len(tokens) + 1)):
                ngram = ' '.join(tokens[i:j])
                ngrams.append(ngram)
        
        # Match against symptom vocabulary
        symptom_names = list(self.symptom_vocabulary.keys())
        
        for ngram in ngrams:
            # Skip very short tokens
            if len(ngram) < 3:
                continue
            
            # Find best matches
            matches = process.extractBests(
                ngram, 
                symptom_names, 
                scorer=fuzz.token_sort_ratio,
                score_cutoff=70,
                limit=3
            )
            
            for match, score in matches:
                confidence = score / 100.0
                
                # Extract additional indicators
                severity_indicators = self._extract_severity_indicators(text)
                temporal_indicators = self._extract_temporal_indicators(text)
                frequency_indicators = self._extract_frequency_indicators(text)
                
                extracted.append(ExtractedSymptom(
                    original_text=ngram,
                    normalized_text=match,
                    confidence=confidence * 0.7,  # Reduce confidence for fuzzy matches
                    severity_indicators=severity_indicators,
                    temporal_indicators=temporal_indicators,
                    location_indicators=[],
                    frequency_indicators=frequency_indicators
                ))
        
        return extracted
    
    def _extract_with_spacy(self, text: str) -> List[ExtractedSymptom]:
        """Extract symptoms using spaCy NLP."""
        if not self.nlp:
            return []
        
        extracted = []
        doc = self.nlp(text)
        
        # Extract medical entities
        for ent in doc.ents:
            if ent.label_ in ['DISEASE', 'SYMPTOM', 'MEDICAL_CONDITION']:
                # Normalize the entity text
                normalized = self._normalize_symptom(ent.text)
                
                extracted.append(ExtractedSymptom(
                    original_text=ent.text,
                    normalized_text=normalized,
                    confidence=0.7,
                    severity_indicators=[],
                    temporal_indicators=[],
                    location_indicators=[],
                    frequency_indicators=[]
                ))
        
        # Extract noun phrases that might be symptoms
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower()
            
            # Check if it matches known symptoms
            best_match = process.extractOne(
                chunk_text, 
                list(self.symptom_vocabulary.keys()),
                scorer=fuzz.token_sort_ratio
            )
            
            if best_match and best_match[1] > 80:
                extracted.append(ExtractedSymptom(
                    original_text=chunk.text,
                    normalized_text=best_match[0],
                    confidence=best_match[1] / 100.0 * 0.6,
                    severity_indicators=[],
                    temporal_indicators=[],
                    location_indicators=[],
                    frequency_indicators=[]
                ))
        
        return extracted
    
    def _extract_with_transformers(self, text: str) -> List[ExtractedSymptom]:
        """Extract symptoms using transformer-based NER."""
        if not self.use_transformers:
            return []
        
        extracted = []
        
        try:
            # Use medical BERT for NER
            entities = self.medical_ner(text)
            
            for entity in entities:
                if entity['entity_group'] in ['DISEASE', 'SYMPTOM']:
                    # Normalize the entity
                    normalized = self._normalize_symptom(entity['word'])
                    
                    extracted.append(ExtractedSymptom(
                        original_text=entity['word'],
                        normalized_text=normalized,
                        confidence=entity['score'],
                        severity_indicators=[],
                        temporal_indicators=[],
                        location_indicators=[],
                        frequency_indicators=[]
                    ))
        
        except Exception as e:
            logger.warning(f"Error in transformer-based extraction: {e}")
        
        return extracted
    
    def _extract_with_semantics(self, text: str) -> List[ExtractedSymptom]:
        """Extract symptoms using semantic similarity."""
        if not self.use_transformers or not hasattr(self, 'sentence_transformer'):
            return []
        
        extracted = []
        
        try:
            # Get sentence embeddings
            text_embedding = self.sentence_transformer.encode([text])
            
            # Compare with symptom embeddings (would be pre-computed in production)
            symptom_names = list(self.symptom_vocabulary.keys())
            symptom_embeddings = self.sentence_transformer.encode(symptom_names)
            
            # Calculate similarities
            similarities = np.dot(text_embedding, symptom_embeddings.T).flatten()
            
            # Get top matches
            top_indices = np.argsort(similarities)[::-1][:5]
            
            for idx in top_indices:
                similarity = similarities[idx]
                if similarity > 0.5:  # Threshold for semantic similarity
                    symptom = symptom_names[idx]
                    
                    extracted.append(ExtractedSymptom(
                        original_text=text,
                        normalized_text=symptom,
                        confidence=similarity * 0.8,  # Reduce confidence for semantic matches
                        severity_indicators=[],
                        temporal_indicators=[],
                        location_indicators=[],
                        frequency_indicators=[]
                    ))
        
        except Exception as e:
            logger.warning(f"Error in semantic extraction: {e}")
        
        return extracted
    
    def _normalize_symptom(self, symptom_text: str) -> str:
        """Normalize symptom text to standard form."""
        # Clean and lowercase
        normalized = symptom_text.lower().strip()
        
        # Remove punctuation
        normalized = normalized.translate(str.maketrans('', '', string.punctuation))
        
        # Replace spaces with underscores
        normalized = normalized.replace(' ', '_')
        
        # Apply synonym mapping
        normalized = self.symptom_synonyms.get(normalized, normalized)
        
        # Handle common variations
        if 'pain' in normalized and any(loc in normalized for loc in ['head', 'chest', 'stomach', 'back']):
            # Extract location
            for location in ['head', 'chest', 'stomach', 'back', 'abdomen']:
                if location in normalized:
                    normalized = f"{location}_pain"
                    break
        
        return normalized
    
    def _extract_severity_indicators(self, text: str) -> List[str]:
        """Extract severity indicators from text."""
        indicators = []
        
        text_lower = text.lower()
        for keyword, weight in self.severity_keywords.items():
            if keyword in text_lower:
                indicators.append(keyword)
        
        # Extract from patterns
        severity_matches = self.medical_patterns['severity_pattern'].findall(text_lower)
        indicators.extend(severity_matches)
        
        return list(set(indicators))
    
    def _extract_temporal_indicators(self, text: str) -> List[str]:
        """Extract temporal indicators from text."""
        indicators = []
        
        text_lower = text.lower()
        for keyword, category in self.temporal_keywords.items():
            if keyword in text_lower:
                indicators.append(category)
        
        # Extract duration patterns
        duration_matches = self.medical_patterns['duration_pattern'].findall(text_lower)
        for match in duration_matches:
            duration = f"{match[0]}_{match[1]}"
            indicators.append(duration)
        
        return list(set(indicators))
    
    def _extract_location_indicators(self, text: str) -> List[str]:
        """Extract anatomical location indicators from text."""
        indicators = []
        
        text_lower = text.lower()
        for keyword, location in self.location_keywords.items():
            if keyword in text_lower:
                indicators.append(location)
        
        return list(set(indicators))
    
    def _extract_frequency_indicators(self, text: str) -> List[str]:
        """Extract frequency indicators from text."""
        indicators = []
        
        text_lower = text.lower()
        for keyword, frequency in self.frequency_keywords.items():
            if keyword in text_lower:
                indicators.append(frequency)
        
        # Extract from patterns
        frequency_matches = self.medical_patterns['frequency_pattern'].findall(text_lower)
        indicators.extend(frequency_matches)
        
        return list(set(indicators))
    
    def _consolidate_symptoms(self, symptoms: List[ExtractedSymptom]) -> List[ExtractedSymptom]:
        """Consolidate duplicate symptoms and merge information."""
        # Group by normalized text
        symptom_groups = {}
        
        for symptom in symptoms:
            key = symptom.normalized_text
            if key not in symptom_groups:
                symptom_groups[key] = []
            symptom_groups[key].append(symptom)
        
        consolidated = []
        
        for normalized_text, group in symptom_groups.items():
            # Take the symptom with highest confidence
            best_symptom = max(group, key=lambda s: s.confidence)
            
            # Merge all indicators
            all_severity = []
            all_temporal = []
            all_location = []
            all_frequency = []
            
            for symptom in group:
                all_severity.extend(symptom.severity_indicators)
                all_temporal.extend(symptom.temporal_indicators)
                all_location.extend(symptom.location_indicators)
                all_frequency.extend(symptom.frequency_indicators)
            
            # Create consolidated symptom
            consolidated_symptom = ExtractedSymptom(
                original_text=best_symptom.original_text,
                normalized_text=normalized_text,
                confidence=best_symptom.confidence,
                severity_indicators=list(set(all_severity)),
                temporal_indicators=list(set(all_temporal)),
                location_indicators=list(set(all_location)),
                frequency_indicators=list(set(all_frequency))
            )
            
            consolidated.append(consolidated_symptom)
        
        # Sort by confidence
        consolidated.sort(key=lambda s: s.confidence, reverse=True)
        
        return consolidated
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment and emotional state from text."""
        try:
            blob = TextBlob(text)
            sentiment = blob.sentiment
            
            # Analyze emotional indicators
            emotional_keywords = {
                'anxiety': ['worried', 'anxious', 'nervous', 'scared', 'afraid'],
                'depression': ['sad', 'depressed', 'hopeless', 'down', 'blue'],
                'frustration': ['frustrated', 'annoyed', 'irritated', 'angry'],
                'fear': ['terrified', 'panicked', 'fearful', 'frightened']
            }
            
            emotions = {}
            text_lower = text.lower()
            
            for emotion, keywords in emotional_keywords.items():
                score = sum(1 for keyword in keywords if keyword in text_lower)
                emotions[emotion] = score / len(keywords)
            
            return {
                'polarity': sentiment.polarity,
                'subjectivity': sentiment.subjectivity,
                'emotions': emotions,
                'urgency_level': self._assess_urgency(text)
            }
        
        except Exception as e:
            logger.warning(f"Error in sentiment analysis: {e}")
            return {'polarity': 0, 'subjectivity': 0, 'emotions': {}, 'urgency_level': 'medium'}
    
    def _assess_urgency(self, text: str) -> str:
        """Assess urgency level from text."""
        urgency_keywords = {
            'high': ['emergency', 'urgent', 'severe', 'unbearable', 'can\'t', 'cannot', 'help'],
            'medium': ['uncomfortable', 'bothersome', 'concerning', 'worried'],
            'low': ['mild', 'slight', 'minor', 'occasional']
        }
        
        text_lower = text.lower()
        scores = {}
        
        for level, keywords in urgency_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[level] = score
        
        if scores['high'] > 0:
            return 'high'
        elif scores['medium'] > scores['low']:
            return 'medium'
        else:
            return 'low'
    
    def get_symptom_suggestions(self, partial_text: str, limit: int = 10) -> List[str]:
        """Get symptom suggestions for autocomplete."""
        if len(partial_text) < 2:
            return []
        
        # Fuzzy match against symptom vocabulary
        matches = process.extractBests(
            partial_text,
            list(self.symptom_vocabulary.keys()),
            scorer=fuzz.partial_ratio,
            score_cutoff=60,
            limit=limit
        )
        
        return [match[0] for match in matches]
