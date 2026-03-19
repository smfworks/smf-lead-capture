"""ML-based lead scoring and predictive routing."""

import json
import logging
import pickle
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


@dataclass
class LeadFeatures:
    """Features extracted from lead data for ML scoring."""
    # Demographic features
    has_name: int
    has_email: int
    has_phone: int
    email_domain_score: float
    
    # Engagement features
    message_length: int
    question_count: int
    exclamation_count: int
    
    # Intent features
    urgency_keywords: int
    budget_mentioned: int
    timeline_mentioned: int
    
    # Source features
    source_score: float
    landing_page_quality: float
    
    # Temporal features
    hour_of_day: int
    day_of_week: int
    is_weekend: int
    is_business_hours: int
    
    # Qualification features
    qualification_completeness: float
    budget_tier: int
    timeline_urgency: int


class MLLeadScorer:
    """Machine learning-based lead scoring system."""
    
    def __init__(self, model_path: str = "models/lead_scorer.pkl"):
        """Initialize ML scorer."""
        self.model_path = Path(model_path)
        self.model = None
        self.scaler = StandardScaler()
        self.text_vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        self.is_trained = False
        
        # Load or initialize model
        self._load_model()
    
    def _load_model(self):
        """Load pre-trained model if exists."""
        if self.model_path.exists():
            try:
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data.get('model')
                    self.scaler = data.get('scaler', StandardScaler())
                    self.is_trained = True
                    logger.info("Loaded ML scoring model")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                self._init_default_model()
        else:
            self._init_default_model()
    
    def _init_default_model(self):
        """Initialize default model (rule-based fallback)."""
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1
        )
        self.is_trained = False
        logger.info("Initialized default ML model")
    
    def _extract_features(self, lead_data: Dict[str, Any]) -> np.ndarray:
        """Extract features from lead data."""
        features = LeadFeatures(
            # Demographic
            has_name=1 if lead_data.get('name') else 0,
            has_email=1 if lead_data.get('email') else 0,
            has_phone=1 if lead_data.get('phone') else 0,
            email_domain_score=self._score_email_domain(lead_data.get('email', '')),
            
            # Engagement
            message_length=len(lead_data.get('message', '')),
            question_count=lead_data.get('message', '').count('?'),
            exclamation_count=lead_data.get('message', '').count('!'),
            
            # Intent
            urgency_keywords=self._count_urgency_keywords(lead_data.get('message', '')),
            budget_mentioned=self._has_budget_mention(lead_data.get('message', '')),
            timeline_mentioned=self._has_timeline_mention(lead_data.get('message', '')),
            
            # Source
            source_score=self._score_source(lead_data.get('source', 'unknown')),
            landing_page_quality=self._score_landing_page(lead_data.get('metadata', {})),
            
            # Temporal
            hour_of_day=datetime.now().hour,
            day_of_week=datetime.now().weekday(),
            is_weekend=1 if datetime.now().weekday() >= 5 else 0,
            is_business_hours=1 if 9 <= datetime.now().hour < 17 else 0,
            
            # Qualification
            qualification_completeness=self._calc_qualification_completeness(lead_data),
            budget_tier=self._extract_budget_tier(lead_data),
            timeline_urgency=self._extract_timeline_urgency(lead_data)
        )
        
        return np.array([
            features.has_name,
            features.has_email,
            features.has_phone,
            features.email_domain_score,
            features.message_length,
            features.question_count,
            features.exclamation_count,
            features.urgency_keywords,
            features.budget_mentioned,
            features.timeline_mentioned,
            features.source_score,
            features.landing_page_quality,
            features.hour_of_day,
            features.day_of_week,
            features.is_weekend,
            features.is_business_hours,
            features.qualification_completeness,
            features.budget_tier,
            features.timeline_urgency
        ])
    
    def _score_email_domain(self, email: str) -> float:
        """Score email domain quality."""
        if not email or '@' not in email:
            return 0.0
        
        domain = email.split('@')[1].lower()
        
        # Personal domains (lower score)
        personal = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']
        if domain in personal:
            return 0.5
        
        # Free/temp domains (very low score)
        temp_domains = ['tempmail.com', '10minutemail.com', 'guerrillamail.com']
        if any(td in domain for td in temp_domains):
            return 0.1
        
        # Business domains (higher score)
        return 1.0
    
    def _count_urgency_keywords(self, message: str) -> int:
        """Count urgency keywords in message."""
        if not message:
            return 0
        
        urgency_words = [
            'urgent', 'asap', 'immediately', 'today', 'now', 'rush',
            'quick', 'fast', 'deadline', 'emergency', 'critical'
        ]
        
        message_lower = message.lower()
        return sum(1 for word in urgency_words if word in message_lower)
    
    def _has_budget_mention(self, message: str) -> int:
        """Check if message mentions budget."""
        if not message:
            return 0
        
        budget_indicators = [
            'budget', 'cost', 'price', 'pricing', '$', 'dollar',
            'afford', 'expensive', 'cheap', 'quote', 'estimate'
        ]
        
        message_lower = message.lower()
        return 1 if any(ind in message_lower for ind in budget_indicators) else 0
    
    def _has_timeline_mention(self, message: str) -> int:
        """Check if message mentions timeline."""
        if not message:
            return 0
        
        timeline_indicators = [
            'timeline', 'deadline', 'when', 'start', 'begin',
            'week', 'month', 'soon', 'quickly', 'date', 'schedule'
        ]
        
        message_lower = message.lower()
        return 1 if any(ind in message_lower for ind in timeline_indicators) else 0
    
    def _score_source(self, source: str) -> float:
        """Score lead source quality."""
        source_scores = {
            'referral': 1.0,
            'organic_search': 0.9,
            'direct': 0.8,
            'email': 0.7,
            'social_media': 0.6,
            'paid_search': 0.5,
            'display_ad': 0.3,
            'unknown': 0.5
        }
        return source_scores.get(source.lower(), 0.5)
    
    def _score_landing_page(self, metadata: Dict) -> float:
        """Score landing page quality."""
        page = metadata.get('landing_page', '')
        
        # High-intent pages
        high_intent = ['/pricing', '/demo', '/contact', '/quote', '/consultation']
        if any(hi in page.lower() for hi in high_intent):
            return 1.0
        
        # Medium-intent pages
        medium_intent = ['/services', '/features', '/solutions', '/case-studies']
        if any(mi in page.lower() for mi in medium_intent):
            return 0.7
        
        # Low-intent pages
        return 0.4
    
    def _calc_qualification_completeness(self, lead_data: Dict) -> float:
        """Calculate qualification data completeness."""
        qualification = lead_data.get('qualification_data', {})
        
        expected_fields = ['timeline', 'budget', 'company_size', 'use_case']
        if not expected_fields:
            return 0.0
        
        filled = sum(1 for f in expected_fields if qualification.get(f))
        return filled / len(expected_fields)
    
    def _extract_budget_tier(self, lead_data: Dict) -> int:
        """Extract budget tier from qualification data."""
        budget = lead_data.get('qualification_data', {}).get('budget', '')
        
        budget_map = {
            'under_5k': 1,
            '5k_to_10k': 2,
            '10k_to_25k': 3,
            '25k_to_50k': 4,
            '50k_plus': 5
        }
        
        return budget_map.get(budget.lower(), 0)
    
    def _extract_timeline_urgency(self, lead_data: Dict) -> int:
        """Extract timeline urgency from qualification data."""
        timeline = lead_data.get('qualification_data', {}).get('timeline', '')
        
        urgency_map = {
            'asap': 5,
            'this_month': 4,
            'next_month': 3,
            'this_quarter': 2,
            'exploring': 1
        }
        
        return urgency_map.get(timeline.lower(), 0)
    
    def score_lead(self, lead_data: Dict[str, Any]) -> Tuple[int, str, Dict[str, float]]:
        """Score a lead using ML model.
        
        Returns:
            Tuple of (score, category, feature_importance)
        """
        features = self._extract_features(lead_data)
        
        if self.is_trained and self.model:
            try:
                # Scale features
                features_scaled = self.scaler.transform(features.reshape(1, -1))
                
                # Predict probability of conversion
                prob = self.model.predict_proba(features_scaled)[0]
                score = int(prob[1] * 100)  # Probability of being high-quality
                
                # Get feature importance
                importance = self._get_feature_importance(features)
            except Exception as e:
                logger.error(f"ML prediction failed: {e}")
                score, importance = self._rule_based_score(features)
        else:
            score, importance = self._rule_based_score(features)
        
        # Determine category
        if score >= 70:
            category = 'hot'
        elif score >= 40:
            category = 'warm'
        else:
            category = 'cold'
        
        return score, category, importance
    
    def _rule_based_score(self, features: np.ndarray) -> Tuple[int, Dict[str, float]]:
        """Fallback rule-based scoring."""
        score = 50  # Base score
        importance = {}
        
        # Contact info (+20 max)
        if features[0]:  # has_name
            score += 5
            importance['has_name'] = 5
        if features[1]:  # has_email
            score += 5
            importance['has_email'] = 5
        if features[2]:  # has_phone
            score += 10
            importance['has_phone'] = 10
        
        # Engagement (+20 max)
        msg_len = features[4]
        if msg_len > 100:
            score += 10
            importance['message_length'] = 10
        if features[6] > 0:  # exclamation
            score += 5
            importance['exclamation_count'] = 5
        
        # Intent (+30 max)
        urgency = features[7]
        if urgency > 0:
            score += min(urgency * 5, 15)
            importance['urgency_keywords'] = min(urgency * 5, 15)
        if features[8]:  # budget mentioned
            score += 10
            importance['budget_mentioned'] = 10
        if features[9]:  # timeline mentioned
            score += 5
            importance['timeline_mentioned'] = 5
        
        # Source (+10 max)
        source_score = features[10]
        score += int(source_score * 10)
        importance['source_score'] = int(source_score * 10)
        
        # Qualification (+20 max)
        completeness = features[16]
        score += int(completeness * 20)
        importance['qualification_completeness'] = int(completeness * 20)
        
        return min(score, 100), importance
    
    def _get_feature_importance(self, features: np.ndarray) -> Dict[str, float]:
        """Get feature importance from model."""
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            feature_names = [
                'has_name', 'has_email', 'has_phone', 'email_domain',
                'message_length', 'questions', 'exclamations',
                'urgency', 'budget_mentioned', 'timeline_mentioned',
                'source', 'landing_page', 'hour', 'day', 'weekend',
                'business_hours', 'qualification', 'budget_tier', 'timeline_urgency'
            ]
            return dict(zip(feature_names, importances))
        return {}
    
    def train(self, leads_data: List[Dict[str, Any]], 
              labels: List[int]) -> Dict[str, Any]:
        """Train the ML model on historical lead data.
        
        Args:
            leads_data: List of lead dictionaries
            labels: List of labels (1 for converted, 0 for not)
            
        Returns:
            Training metrics
        """
        try:
            # Extract features for all leads
            X = np.array([self._extract_features(lead) for lead in leads_data])
            y = np.array(labels)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model = GradientBoostingClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)
            
            self.is_trained = True
            
            # Save model
            self._save_model()
            
            return {
                'train_accuracy': train_score,
                'test_accuracy': test_score,
                'n_samples': len(leads_data),
                'n_features': X.shape[1]
            }
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {'error': str(e)}
    
    def _save_model(self):
        """Save trained model to disk."""
        try:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'scaler': self.scaler
                }, f)
            logger.info(f"Saved model to {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")


class PredictiveRouter:
    """Predictive lead routing based on agent performance and lead characteristics."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize predictive router."""
        self.config = config
        self.agent_performance = {}
        self.specialization_weights = {}
    
    def route_lead(self, lead_data: Dict[str, Any], 
                   available_agents: List[Dict[str, Any]]) -> Optional[str]:
        """Route lead to best available agent.
        
        Returns:
            Agent ID or None if no match
        """
        if not available_agents:
            return None
        
        scores = []
        
        for agent in available_agents:
            score = self._calculate_agent_score(agent, lead_data)
            scores.append((agent['id'], score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[0][0] if scores else None
    
    def _calculate_agent_score(self, agent: Dict[str, Any], 
                              lead_data: Dict[str, Any]) -> float:
        """Calculate match score for agent-lead pair."""
        score = 50.0  # Base score
        
        # Agent availability
        if agent.get('status') != 'available':
            score -= 30
        
        # Current load (prefer less busy agents)
        current_leads = agent.get('active_leads', 0)
        score -= current_leads * 5
        
        # Specialization match
        agent_specs = set(agent.get('specializations', []))
        lead_category = lead_data.get('score_category', 'cold')
        
        if lead_category in agent_specs:
            score += 20
        
        # Historical performance
        agent_id = agent['id']
        if agent_id in self.agent_performance:
            perf = self.agent_performance[agent_id]
            conversion_rate = perf.get('conversion_rate', 0.3)
            score += conversion_rate * 30
        
        # Response time (faster is better)
        avg_response_time = agent.get('avg_response_time', 60)
        if avg_response_time < 5:
            score += 10
        elif avg_response_time < 15:
            score += 5
        
        return score
    
    def update_agent_performance(self, agent_id: str, 
                                 lead_id: str, 
                                 converted: bool):
        """Update agent performance metrics."""
        if agent_id not in self.agent_performance:
            self.agent_performance[agent_id] = {
                'total_leads': 0,
                'conversions': 0,
                'conversion_rate': 0.0
            }
        
        perf = self.agent_performance[agent_id]
        perf['total_leads'] += 1
        if converted:
            perf['conversions'] += 1
        
        perf['conversion_rate'] = perf['conversions'] / perf['total_leads']
    
    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get agent performance statistics."""
        return self.agent_performance.get(agent_id, {
            'total_leads': 0,
            'conversions': 0,
            'conversion_rate': 0.0
        })