import numpy as np
import pandas as pd
import joblib
import json
import cv2
import librosa
import librosa.display
from PIL import Image
import io
import tempfile
import os
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.feature_selection import SelectKBest, f_classif
import warnings
warnings.filterwarnings('ignore')

class SpiralDrawingProcessor:
    """Process spiral drawing images for Parkinson's detection"""
    
    @staticmethod
    def preprocess_image(image_path, target_size=(256, 256)):
        """Preprocess spiral drawing image"""
        try:
            # Load image
            if isinstance(image_path, str):
                img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            else:
                # Handle file object
                img_array = np.frombuffer(image_path.read(), np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
            
            if img is None:
                raise ValueError("Could not load image")
            
            # Resize
            img = cv2.resize(img, target_size)
            
            # Apply threshold
            _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
            
            # Get largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Extract features
            features = SpiralDrawingProcessor.extract_features(largest_contour, img)
            
            return features
            
        except Exception as e:
            print(f"Error processing spiral image: {e}")
            return None
    
    @staticmethod
    def extract_features(contour, image):
        """Extract features from spiral contour"""
        features = {}
        
        # Basic contour features
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        features['area'] = area
        features['perimeter'] = perimeter
        features['circularity'] = (4 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 0
        
        # Bounding box features
        x, y, w, h = cv2.boundingRect(contour)
        features['aspect_ratio'] = w / h if h > 0 else 0
        features['bounding_box_area'] = w * h
        features['filled_ratio'] = area / (w * h) if (w * h) > 0 else 0
        
        # Smoothness features (using Hu moments)
        moments = cv2.moments(contour)
        hu_moments = cv2.HuMoments(moments).flatten()
        for i in range(7):
            features[f'hu_moment_{i}'] = -1 * np.sign(hu_moments[i]) * np.log10(abs(hu_moments[i])) if abs(hu_moments[i]) > 0 else 0
        
        # Tremor analysis (simplified)
        # Calculate distance from contour points to centroid
        M = cv2.moments(contour)
        if M['m00'] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            
            distances = []
            for point in contour:
                x, y = point[0]
                dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                distances.append(dist)
            
            if distances:
                features['distance_mean'] = np.mean(distances)
                features['distance_std'] = np.std(distances)
                features['distance_variance'] = np.var(distances)
        
        return features

class VoiceProcessor:
    """Process voice recordings for Parkinson's detection"""
    
    @staticmethod
    def extract_features(audio_path, sr=22050):
        """Extract audio features from voice recording"""
        try:
            # Load audio file
            if isinstance(audio_path, str):
                y, sr = librosa.load(audio_path, sr=sr)
            else:
                # Handle file object
                y, sr = librosa.load(io.BytesIO(audio_path.read()), sr=sr)
            
            features = {}
            
            # Basic audio features
            features['duration'] = len(y) / sr
            
            # Time-domain features
            features['amplitude_mean'] = np.mean(np.abs(y))
            features['amplitude_std'] = np.std(y)
            features['zero_crossing_rate'] = np.mean(librosa.feature.zero_crossing_rate(y))
            
            # Frequency-domain features
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
            features['spectral_centroid_mean'] = np.mean(spectral_centroid)
            features['spectral_centroid_std'] = np.std(spectral_centroid)
            
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
            features['spectral_bandwidth_mean'] = np.mean(spectral_bandwidth)
            
            # MFCC features
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            for i in range(13):
                features[f'mfcc_{i}_mean'] = np.mean(mfccs[i])
                features[f'mfcc_{i}_std'] = np.std(mfccs[i])
            
            # Jitter and Shimmer (simplified approximations)
            # Note: Real jitter/shimmer calculation requires pitch detection
            # This is a simplified version
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitches = pitches[pitches > 0]
            if len(pitches) > 1:
                features['pitch_mean'] = np.mean(pitches)
                features['pitch_std'] = np.std(pitches)
                # Approximate jitter as pitch variation
                features['jitter'] = np.std(np.diff(pitches)) / np.mean(pitches) if np.mean(pitches) > 0 else 0
            else:
                features['pitch_mean'] = 0
                features['pitch_std'] = 0
                features['jitter'] = 0
            
            # Harmonics-to-noise ratio approximation
            S = np.abs(librosa.stft(y))
            harmonics = librosa.effects.harmonic(y)
            H = np.abs(librosa.stft(harmonics))
            noise = y - harmonics
            N = np.abs(librosa.stft(noise))
            features['hnr'] = np.mean(H) / np.mean(N) if np.mean(N) > 0 else 0
            
            return features
            
        except Exception as e:
            print(f"Error processing audio: {e}")
            return None

class MRIImageProcessor:
    """Process MRI images for Parkinson's detection"""
    
    @staticmethod
    def preprocess_image(image_path, target_size=(224, 224)):
        """Preprocess MRI image for CNN"""
        try:
            if isinstance(image_path, str):
                img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            else:
                img_array = np.frombuffer(image_path.read(), np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
            
            if img is None:
                raise ValueError("Could not load MRI image")
            
            # Resize
            img = cv2.resize(img, target_size)
            
            # Normalize
            img = img / 255.0
            
            # Expand dimensions for CNN
            img = np.expand_dims(img, axis=-1)
            img = np.expand_dims(img, axis=0)
            
            return img
            
        except Exception as e:
            print(f"Error processing MRI image: {e}")
            return None

class SymptomQuizProcessor:
    """Process symptom quiz data"""
    
    @staticmethod
    def calculate_features(quiz_data):
        """Calculate features from quiz responses"""
        features = {}
        
        # Motor symptoms score
        motor_score = quiz_data.get('tremor', 0) + quiz_data.get('bradykinesia', 0) + \
                      quiz_data.get('rigidity', 0) + quiz_data.get('postural_instability', 0)
        features['motor_score'] = motor_score
        
        # Non-motor symptoms count
        non_motor_count = sum([
            quiz_data.get('sleep_problems', False),
            quiz_data.get('depression', False),
            quiz_data.get('anxiety', False),
            quiz_data.get('cognitive_changes', False)
        ])
        features['non_motor_count'] = non_motor_count
        
        # Functional impact
        features['daily_activities'] = quiz_data.get('daily_activities', 0)
        
        # Duration multiplier
        duration_multiplier = quiz_data.get('symptom_duration', 1) * 0.5
        features['duration_multiplier'] = duration_multiplier
        
        # Total score
        total_score = (motor_score + (non_motor_count * 2) + (features['daily_activities'] * 2)) * duration_multiplier
        features['total_score'] = min(total_score, 100)
        
        return features

class ParkinsonPredictor:
    """Main predictor class for Parkinson's disease"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.load_models()
    
    def load_models(self):
        """Load trained models"""
        try:
            # Load spiral model
            spiral_model_path = os.path.join(settings.BASE_DIR, 'ai_models', 'trained_models', 'spiral_model.pkl')
            if os.path.exists(spiral_model_path):
                self.models['spiral'] = joblib.load(spiral_model_path)
            
            # Load voice model
            voice_model_path = os.path.join(settings.BASE_DIR, 'ai_models', 'trained_models', 'voice_model.pkl')
            if os.path.exists(voice_model_path):
                self.models['voice'] = joblib.load(voice_model_path)
            
            # Load quiz model
            quiz_model_path = os.path.join(settings.BASE_DIR, 'ai_models', 'trained_models', 'quiz_model.pkl')
            if os.path.exists(quiz_model_path):
                self.models['quiz'] = joblib.load(quiz_model_path)
            
            # Load scalers
            for model_type in ['spiral', 'voice', 'quiz']:
                scaler_path = os.path.join(settings.BASE_DIR, 'ai_models', 'trained_scalers', f'{model_type}_scaler.pkl')
                if os.path.exists(scaler_path):
                    self.scalers[model_type] = joblib.load(scaler_path)
                    
        except Exception as e:
            print(f"Error loading models: {e}")
    
    def predict_spiral(self, drawing_features):
        """Predict from spiral drawing"""
        try:
            if 'spiral' not in self.models:
                return self._simulate_prediction('spiral')
            
            # Prepare features
            feature_vector = self._prepare_features(drawing_features, 'spiral')
            
            if feature_vector is None:
                return self._simulate_prediction('spiral')
            
            # Make prediction
            prediction = self.models['spiral'].predict(feature_vector)[0]
            probability = self.models['spiral'].predict_proba(feature_vector)[0]
            
            return {
                'prediction': bool(prediction),
                'confidence': float(max(probability)),
                'probabilities': probability.tolist(),
                'model_used': 'spiral'
            }
            
        except Exception as e:
            print(f"Error in spiral prediction: {e}")
            return self._simulate_prediction('spiral')
    
    def predict_voice(self, voice_features):
        """Predict from voice recording"""
        try:
            if 'voice' not in self.models:
                return self._simulate_prediction('voice')
            
            # Prepare features
            feature_vector = self._prepare_features(voice_features, 'voice')
            
            if feature_vector is None:
                return self._simulate_prediction('voice')
            
            # Make prediction
            prediction = self.models['voice'].predict(feature_vector)[0]
            probability = self.models['voice'].predict_proba(feature_vector)[0]
            
            return {
                'prediction': bool(prediction),
                'confidence': float(max(probability)),
                'probabilities': probability.tolist(),
                'model_used': 'voice'
            }
            
        except Exception as e:
            print(f"Error in voice prediction: {e}")
            return self._simulate_prediction('voice')
    
    def predict_quiz(self, quiz_features):
        """Predict from symptom quiz"""
        try:
            if 'quiz' not in self.models:
                return self._simulate_prediction('quiz')
            
            # Prepare features
            feature_vector = self._prepare_features(quiz_features, 'quiz')
            
            if feature_vector is None:
                return self._simulate_prediction('quiz')
            
            # Make prediction
            prediction = self.models['quiz'].predict(feature_vector)[0]
            probability = self.models['quiz'].predict_proba(feature_vector)[0]
            
            return {
                'prediction': bool(prediction),
                'confidence': float(max(probability)),
                'probabilities': probability.tolist(),
                'model_used': 'quiz'
            }
            
        except Exception as e:
            print(f"Error in quiz prediction: {e}")
            return self._simulate_prediction('quiz')
    
    def ensemble_predict(self, predictions_list):
        """Combine predictions from multiple models"""
        try:
            if not predictions_list:
                return self._simulate_prediction('ensemble')
            
            # Weighted average based on confidence
            total_weight = 0
            weighted_sum = 0
            
            for pred in predictions_list:
                confidence = pred.get('confidence', 0.5)
                prediction = pred.get('prediction', False)
                
                weight = confidence
                total_weight += weight
                weighted_sum += (1 if prediction else 0) * weight
            
            if total_weight > 0:
                final_prob = weighted_sum / total_weight
                final_prediction = final_prob > 0.5
                final_confidence = final_prob if final_prediction else 1 - final_prob
            else:
                final_prediction = False
                final_confidence = 0.5
            
            return {
                'prediction': final_prediction,
                'confidence': final_confidence,
                'probabilities': [1 - final_confidence, final_confidence],
                'model_used': 'ensemble',
                'component_predictions': predictions_list
            }
            
        except Exception as e:
            print(f"Error in ensemble prediction: {e}")
            return self._simulate_prediction('ensemble')
    
    def _prepare_features(self, features_dict, model_type):
        """Prepare features for model prediction"""
        try:
            if model_type in self.scalers:
                # Convert dict to ordered array
                if model_type == 'spiral':
                    feature_order = [
                        'area', 'perimeter', 'circularity', 'aspect_ratio',
                        'bounding_box_area', 'filled_ratio', 'distance_std'
                    ]
                elif model_type == 'voice':
                    feature_order = [
                        'jitter', 'hnr', 'zero_crossing_rate',
                        'spectral_centroid_std', 'pitch_std'
                    ]
                elif model_type == 'quiz':
                    feature_order = ['motor_score', 'non_motor_count', 'total_score']
                else:
                    return None
                
                # Extract features in correct order
                feature_array = []
                for feature in feature_order:
                    feature_array.append(features_dict.get(feature, 0))
                
                feature_array = np.array(feature_array).reshape(1, -1)
                
                # Scale features
                scaled_features = self.scalers[model_type].transform(feature_array)
                return scaled_features
                
            return None
            
        except Exception as e:
            print(f"Error preparing features: {e}")
            return None
    
    def _simulate_prediction(self, model_type):
        """Simulate prediction when model is not available"""
        import random
        
        # Simulate some realistic probabilities
        if model_type == 'spiral':
            prob = random.uniform(0.3, 0.8)
        elif model_type == 'voice':
            prob = random.uniform(0.4, 0.85)
        elif model_type == 'quiz':
            prob = random.uniform(0.5, 0.9)
        else:
            prob = random.uniform(0.6, 0.95)
        
        prediction = prob > 0.6
        confidence = prob if prediction else 1 - prob
        
        return {
            'prediction': prediction,
            'confidence': confidence,
            'probabilities': [1 - prob, prob],
            'model_used': f'{model_type}_simulated',
            'simulated': True
        }