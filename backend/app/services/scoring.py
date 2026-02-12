import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class CallScoringEngine:
    """Intelligent call quality scoring system"""
    
    def __init__(self):
        # Greeting phrases
        self.greeting_phrases = [
            'good morning', 'good afternoon', 'good evening',
            'thank you for calling', 'how can i help', 'how may i assist',
            'welcome to', 'this is', 'my name is'
        ]
        
        # Compliance keywords
        self.compliance_keywords = [
            'confirm', 'verify', 'understand', 'consent', 'agree',
            'terms and conditions', 'privacy policy', 'authorization',
            'recorded', 'documentation', 'policy'
        ]
        
        # Positive indicators
        self.positive_words = [
            'absolutely', 'certainly', 'definitely', 'of course',
            'happy to help', 'glad to assist', 'pleasure', 'excellent'
        ]
        
        # Negative indicators
        self.negative_words = [
            'unfortunately', 'sorry', 'apologize', 'issue', 'problem',
            'error', 'mistake', 'delay', 'inconvenience'
        ]
        
        # Resolution phrases
        self.resolution_phrases = [
            'resolved', 'fixed', 'completed', 'done', 'taken care of',
            'will follow up', 'will send', 'scheduled', 'arranged'
        ]
    
    def score_call(
        self,
        transcript: str,
        sentiment: str,
        sentiment_score: float,
        duration: int = None,
        customer_messages: List[str] = None
    ) -> Dict:
        """
        Score call quality on multiple dimensions
        
        Args:
            transcript: Full call transcript
            sentiment: Overall sentiment (positive/neutral/negative/angry)
            sentiment_score: Sentiment score (-1 to 1)
            duration: Call duration in seconds
            customer_messages: List of customer messages for analysis
            
        Returns:
            Dict with detailed scoring breakdown
        """
        transcript_lower = transcript.lower()
        
        # 1. Greeting Quality (0-10)
        greeting_score = self._score_greeting(transcript_lower)
        
        # 2. Compliance Score (0-20)
        compliance_score = self._score_compliance(transcript_lower)
        
        # 3. Customer Satisfaction (0-30)
        satisfaction_score = self._score_satisfaction(
            sentiment, sentiment_score, customer_messages
        )
        
        # 4. Call Clarity (0-20)
        clarity_score = self._score_clarity(transcript, duration)
        
        # 5. Resolution Score (0-20)
        resolution_score = self._score_resolution(transcript_lower)
        
        # Calculate total
        total_score = (
            greeting_score +
            compliance_score +
            satisfaction_score +
            clarity_score +
            resolution_score
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(
            total_score, sentiment, satisfaction_score
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            greeting_score, compliance_score, satisfaction_score,
            clarity_score, resolution_score
        )
        
        return {
            "total_score": total_score,
            "greeting_quality": greeting_score,
            "compliance_score": compliance_score,
            "customer_satisfaction": satisfaction_score,
            "call_clarity": clarity_score,
            "resolution_score": resolution_score,
            "risk_level": risk_level,
            "recommendations": recommendations
        }
    
    def _score_greeting(self, transcript: str) -> int:
        """Score greeting quality (0-10)"""
        # Check first 200 characters
        intro = transcript[:200]
        
        score = 0
        greeting_found = any(phrase in intro for phrase in self.greeting_phrases)
        
        if greeting_found:
            score = 7
            
            # Bonus for professional introduction
            if 'my name is' in intro or 'this is' in intro:
                score += 2
            
            # Bonus for thank you
            if 'thank you' in intro:
                score += 1
        else:
            score = 3  # Some points for at least starting the call
        
        return min(score, 10)
    
    def _score_compliance(self, transcript: str) -> int:
        """Score compliance keyword usage (0-20)"""
        score = 0
        keywords_found = 0
        
        for keyword in self.compliance_keywords:
            if keyword in transcript:
                keywords_found += 1
        
        # Each keyword worth ~3 points, max 20
        score = min(keywords_found * 3, 20)
        
        return score
    
    def _score_satisfaction(
        self,
        sentiment: str,
        sentiment_score: float,
        customer_messages: List[str] = None
    ) -> int:
        """Score customer satisfaction (0-30)"""
        base_score = {
            'positive': 30,
            'neutral': 20,
            'negative': 10,
            'angry': 5
        }.get(sentiment, 15)
        
        # Adjust based on sentiment score
        if sentiment_score > 0.5:
            base_score = min(base_score + 5, 30)
        elif sentiment_score < -0.5:
            base_score = max(base_score - 5, 0)
        
        return base_score
    
    def _score_clarity(self, transcript: str, duration: int = None) -> int:
        """Score call clarity (0-20)"""
        score = 15  # Base score
        
        # Deduct for very short calls (may indicate confusion)
        if duration and duration < 30:
            score -= 5
        
        # Deduct for excessive filler words
        filler_count = len(re.findall(r'\b(um|uh|like|you know)\b', transcript.lower()))
        if filler_count > 20:
            score -= 3
        elif filler_count > 10:
            score -= 2
        
        # Bonus for positive indicators
        positive_count = sum(1 for word in self.positive_words if word in transcript.lower())
        if positive_count > 3:
            score += 3
        
        return max(0, min(score, 20))
    
    def _score_resolution(self, transcript: str) -> int:
        """Score problem resolution (0-20)"""
        score = 10  # Base score
        
        # Check for resolution phrases
        resolution_found = any(phrase in transcript for phrase in self.resolution_phrases)
        
        if resolution_found:
            score += 10
        
        # Deduct for unresolved indicators
        unresolved_words = ['still', 'waiting', 'not fixed', 'no solution', 'unresolved']
        if any(word in transcript for word in unresolved_words):
            score -= 5
        
        return max(0, min(score, 20))
    
    def _determine_risk_level(
        self,
        total_score: int,
        sentiment: str,
        satisfaction_score: int
    ) -> str:
        """Determine risk level based on scores"""
        if sentiment == 'angry' or total_score < 40:
            return 'high'
        elif sentiment == 'negative' or total_score < 60:
            return 'medium'
        else:
            return 'low'
    
    def _generate_recommendations(
        self,
        greeting: int,
        compliance: int,
        satisfaction: int,
        clarity: int,
        resolution: int
    ) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if greeting < 7:
            recommendations.append("Improve call opening with professional greeting")
        
        if compliance < 12:
            recommendations.append("Use more compliance keywords (verify, confirm, consent)")
        
        if satisfaction < 20:
            recommendations.append("Focus on improving customer satisfaction and tone")
        
        if clarity < 15:
            recommendations.append("Reduce filler words and improve call clarity")
        
        if resolution < 15:
            recommendations.append("Clearly communicate resolution steps and follow-up actions")
        
        if not recommendations:
            recommendations.append("Excellent call quality - maintain current standards")
        
        return recommendations


# Global instance
_scoring_engine = None


def get_scoring_engine() -> CallScoringEngine:
    """Get or create scoring engine singleton"""
    global _scoring_engine
    if _scoring_engine is None:
        _scoring_engine = CallScoringEngine()
    return _scoring_engine
