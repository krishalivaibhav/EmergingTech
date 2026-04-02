"""
Machine Learning-based Resume Analysis using scikit-learn.
Implements:
- TF-IDF vectorization for skill matching
- Cosine similarity for resume-job fit
- Resume quality classification (Logistic Regression)
- Skill gap prediction and clustering
"""

import numpy as np
import pickle
import os
import logging
from typing import Dict, List, Tuple, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import json

logger = logging.getLogger(__name__)

# ML Model persistence directory
MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

TFIDF_MODEL_PATH = os.path.join(MODEL_DIR, 'tfidf_vectorizer.pkl')
QUALITY_CLASSIFIER_PATH = os.path.join(MODEL_DIR, 'quality_classifier.pkl')
SCALER_PATH = os.path.join(MODEL_DIR, 'feature_scaler.pkl')


class MLResumeAnalyzer:
    """ML-powered resume analysis using scikit-learn."""
    
    def __init__(self):
        """Initialize ML models (train if not exists)."""
        self.tfidf_vectorizer = None
        self.quality_classifier = None
        self.feature_scaler = None
        self.skill_database = self._build_skill_database()
        
        # Load or train models
        self._load_or_train_models()
    
    def _build_skill_database(self) -> Dict[str, List[str]]:
        """Build comprehensive skill database for various roles."""
        return {
            'ml_engineer': [
                'python', 'tensorflow', 'pytorch', 'keras', 'scikit-learn',
                'pandas', 'numpy', 'opencv', 'nlp', 'deep learning',
                'machine learning', 'mlops', 'docker', 'kubernetes',
                'aws sagemaker', 'gcp vertex', 'azure ml', 'model deployment',
                'jupyter', 'git', 'sql', 'feature engineering', 'data pipeline'
            ],
            'data_scientist': [
                'python', 'r', 'sql', 'pandas', 'numpy', 'scikit-learn',
                'matplotlib', 'seaborn', 'tableau', 'power bi', 'statistics',
                'probability', 'data visualization', 'data cleaning', 'eda',
                'a/b testing', 'statistical analysis', 'hadoop', 'spark',
                'jupyter', 'git', 'aws', 'gcp', 'azure'
            ],
            'backend_engineer': [
                'python', 'java', 'golang', 'rust', 'nodejs',
                'fastapi', 'django', 'spring boot', 'microservices',
                'rest api', 'graphql', 'sql', 'postgresql', 'mongodb',
                'redis', 'docker', 'kubernetes', 'docker-compose',
                'git', 'ci/cd', 'jenkins', 'github actions', 'aws',
                'gcp', 'azure', 'linux'
            ],
            'frontend_engineer': [
                'javascript', 'typescript', 'react', 'vue', 'angular',
                'html', 'css', 'scss', 'tailwind', 'bootstrap',
                'webpack', 'vite', 'babel', 'npm', 'yarn',
                'git', 'figma', 'ui/ux', 'responsive design',
                'accessibility', 'performance optimization', 'testing',
                'jest', 'react testing library'
            ],
            'devops_engineer': [
                'docker', 'kubernetes', 'terraform', 'ansible',
                'jenkins', 'gitlab ci', 'github actions', 'circleci',
                'aws', 'gcp', 'azure', 'linux', 'shell scripting',
                'python', 'git', 'monitoring', 'prometheus', 'grafana',
                'elk stack', 'datadog', 'infrastructure as code',
                'load balancing', 'nginx', 'apache'
            ]
        }
    
    def _load_or_train_models(self):
        """Load pre-trained models or train new ones."""
        if self._models_exist():
            self._load_models()
            logger.info("✓ ML models loaded from disk")
        else:
            self._train_models()
            self._save_models()
            logger.info("✓ ML models trained and saved")
    
    def _models_exist(self) -> bool:
        """Check if models are already trained."""
        return (os.path.exists(TFIDF_MODEL_PATH) and 
                os.path.exists(QUALITY_CLASSIFIER_PATH) and
                os.path.exists(SCALER_PATH))
    
    def _train_models(self):
        """Train ML models on synthetic resume data."""
        logger.info("Training ML models...")
        
        # Training data: skill combinations for different resume quality levels
        training_resumes = [
            # High quality (label=1)
            'python java kotlin spring boot microservices rest api postgresql docker kubernetes git ci/cd aws',
            'python tensorflow pytorch deep learning mlops docker kubernetes gcp aws model deployment',
            'javascript typescript react vue webpack tailwind testing jest responsive design performance',
            'golang rust systems programming linux shell scripting performance optimization',
            'python pandas numpy scikit-learn eda statistics a/b testing hadoop spark sql',
            'docker kubernetes terraform ansible aws gcp azure infrastructure as code monitoring',
            'python fastapi django sql postgresql mongodb redis git testing ci/cd deployment',
            'typescript react nextjs tailwind jest testing accessibility performance webpack',
            
            # Medium quality (label=0)
            'python java basic programming',
            'javascript html css frontend basics',
            'sql database basics programming',
            'git version control basics',
            
            # Low quality (label=0)
            'coding programming',
            'software development',
            'technology skills',
        ]
        
        training_labels = [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
        
        # Train TF-IDF vectorizer
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1
        )
        X_tfidf = self.tfidf_vectorizer.fit_transform(training_resumes)
        
        # Train quality classifier on TF-IDF features
        self.feature_scaler = StandardScaler(with_mean=False)
        X_scaled = self.feature_scaler.fit_transform(X_tfidf)
        
        self.quality_classifier = LogisticRegression(
            max_iter=1000,
            random_state=42,
            C=1.0
        )
        self.quality_classifier.fit(X_scaled, training_labels)
        
        logger.info(f"  - TF-IDF Vectorizer: {len(self.tfidf_vectorizer.get_feature_names_out())} features")
        logger.info(f"  - Quality Classifier: Logistic Regression trained on {len(training_resumes)} samples")
    
    def _save_models(self):
        """Save trained models to disk."""
        pickle.dump(self.tfidf_vectorizer, open(TFIDF_MODEL_PATH, 'wb'))
        pickle.dump(self.quality_classifier, open(QUALITY_CLASSIFIER_PATH, 'wb'))
        pickle.dump(self.feature_scaler, open(SCALER_PATH, 'wb'))
        logger.info(f"  - Models saved to {MODEL_DIR}")
    
    def _load_models(self):
        """Load pre-trained models from disk."""
        self.tfidf_vectorizer = pickle.load(open(TFIDF_MODEL_PATH, 'rb'))
        self.quality_classifier = pickle.load(open(QUALITY_CLASSIFIER_PATH, 'rb'))
        self.feature_scaler = pickle.load(open(SCALER_PATH, 'rb'))
    
    def predict_resume_quality(self, resume_text: str) -> Dict[str, Any]:
        """
        Predict resume quality (0-100) using trained classifier.
        ML Pipeline: Text → TF-IDF → Scaling → Logistic Regression → Probability
        """
        try:
            # TF-IDF vectorization
            X_tfidf = self.tfidf_vectorizer.transform([resume_text])
            
            # Scale features
            X_scaled = self.feature_scaler.transform(X_tfidf)
            
            # Predict quality probability
            probability = self.quality_classifier.predict_proba(X_scaled)[0][1]
            quality_score = int(probability * 100)
            quality_score = max(20, min(100, quality_score))  # Clamp to 20-100
            
            # Get feature importance insights
            top_features = self._get_top_features(X_tfidf)
            
            return {
                'method': 'ml_classifier',
                'quality_score': quality_score,
                'confidence': float(probability),
                'quality_level': self._score_to_level(quality_score),
                'top_keywords': top_features,
                'model': 'Logistic Regression (TF-IDF)'
            }
        except Exception as e:
            logger.error(f"ML quality prediction error: {str(e)}")
            return None
    
    def _get_top_features(self, X_tfidf) -> List[str]:
        """Extract top TF-IDF features from vectorized text."""
        feature_names = self.tfidf_vectorizer.get_feature_names_out()
        scores = X_tfidf.toarray()[0]
        top_indices = np.argsort(scores)[-5:][::-1]
        return [feature_names[i] for i in top_indices if scores[i] > 0]
    
    def _score_to_level(self, score: int) -> str:
        """Convert numeric score to quality level."""
        if score >= 80:
            return 'Excellent'
        elif score >= 60:
            return 'Good'
        elif score >= 40:
            return 'Fair'
        else:
            return 'Needs Improvement'
    
    def compute_skill_matching(self, resume_text: str, job_description: str, 
                              role: str = 'ml_engineer') -> Dict[str, Any]:
        """
        ML-based skill matching using cosine similarity.
        ML Pipeline: Resume & JD → TF-IDF vectors → Cosine Similarity → Skill Analysis
        """
        try:
            # Vectorize both texts
            vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
            texts = [resume_text, job_description]
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Compute cosine similarity
            similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            # Get role-specific skills
            role_skills = self.skill_database.get(role, self.skill_database['ml_engineer'])
            
            # Find matched and missing skills
            resume_lower = resume_text.lower()
            matched_skills = [skill for skill in role_skills if skill in resume_lower]
            missing_skills = [skill for skill in role_skills if skill not in resume_lower]
            
            match_percentage = (len(matched_skills) / max(len(role_skills), 1)) * 100
            
            return {
                'method': 'ml_cosine_similarity',
                'semantic_similarity': float(similarity_score),
                'skill_match_percentage': float(match_percentage),
                'matched_skills': matched_skills[:10],
                'missing_skills': missing_skills[:5],
                'matched_count': len(matched_skills),
                'total_role_skills': len(role_skills),
                'model': 'TF-IDF + Cosine Similarity'
            }
        except Exception as e:
            logger.error(f"ML skill matching error: {str(e)}")
            return None
    
    def cluster_skill_profiles(self, resumes: List[str]) -> Dict[str, Any]:
        """
        Cluster resumes by skill similarity.
        ML Pipeline: Multiple resumes → TF-IDF → Cosine Similarity Matrix → Clustering insights
        """
        try:
            if len(resumes) < 2:
                return None
            
            vectorizer = TfidfVectorizer(max_features=300, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(resumes)
            
            # Compute similarity matrix for all resume pairs
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Find most similar resume pairs
            similarities = []
            for i in range(len(resumes)):
                for j in range(i + 1, len(resumes)):
                    similarities.append({
                        'resume_1_idx': i,
                        'resume_2_idx': j,
                        'similarity': float(similarity_matrix[i][j])
                    })
            
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            return {
                'method': 'ml_clustering',
                'total_resumes': len(resumes),
                'avg_similarity': float(np.mean(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)])),
                'top_similar_pairs': similarities[:3],
                'model': 'TF-IDF Cosine Similarity Matrix'
            }
        except Exception as e:
            logger.error(f"ML clustering error: {str(e)}")
            return None
    
    def extract_features(self, resume_text: str) -> Dict[str, Any]:
        """
        Extract ML-based features from resume for analysis.
        Includes: word count, skill density, keyword frequency, etc.
        """
        try:
            words = resume_text.lower().split()
            unique_words = set(words)
            
            # Detect technical keywords
            tech_keywords = [
                'python', 'java', 'javascript', 'sql', 'docker', 'kubernetes',
                'aws', 'azure', 'gcp', 'git', 'rest', 'api', 'database',
                'ml', 'ai', 'deep learning', 'tensorflow', 'pytorch'
            ]
            
            detected_keywords = [kw for kw in tech_keywords if kw in resume_text.lower()]
            
            # Calculate feature metrics
            features = {
                'word_count': len(words),
                'unique_words': len(unique_words),
                'vocabulary_richness': len(unique_words) / max(len(words), 1),
                'tech_keyword_count': len(detected_keywords),
                'detected_keywords': detected_keywords,
                'avg_word_length': np.mean([len(w) for w in words]) if words else 0,
                'technical_density': len(detected_keywords) / max(len(words), 1) * 100
            }
            
            return {
                'method': 'ml_feature_extraction',
                'features': features,
                'analysis': 'NLP feature engineering for resume characterization'
            }
        except Exception as e:
            logger.error(f"Feature extraction error: {str(e)}")
            return None


# Singleton instance
_ml_analyzer = None

def get_ml_analyzer() -> MLResumeAnalyzer:
    """Get or create ML analyzer singleton."""
    global _ml_analyzer
    if _ml_analyzer is None:
        _ml_analyzer = MLResumeAnalyzer()
    return _ml_analyzer
