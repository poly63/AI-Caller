from typing import Dict
import logging

logger = logging.getLogger(__name__)

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
except ImportError:
    pipeline = None
    AutoTokenizer = None
    AutoModelForSequenceClassification = None

try:
    import torch
except ImportError:
    torch = None


class SentimentAnalyzer:
    """Sentiment analysis for call transcripts"""
    
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        """
        Initialize sentiment analysis model
        
        Args:
            model_name: HuggingFace model name
        """
        logger.info(f"Loading sentiment model: {model_name}")
        self.sentiment_pipeline = None

        if pipeline and AutoTokenizer and AutoModelForSequenceClassification:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            has_cuda = bool(torch and torch.cuda.is_available())
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if has_cuda else -1
            )
        else:
            logger.warning("transformers/torch not installed; using rule-based sentiment fallback")
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict with sentiment, score, and confidence
        """
        if not text or len(text.strip()) == 0:
            return {
                "sentiment": "neutral",
                "score": 0.0,
                "confidence": 0.0
            }
        
        try:
            if self.sentiment_pipeline is None:
                return self._fallback_sentiment(text)

            # Truncate text if too long
            max_length = 512
            if len(text) > max_length:
                text = text[:max_length]
            
            result = self.sentiment_pipeline(text)[0]
            
            # Map labels to our sentiment categories
            label = result['label'].lower()
            confidence = result['score']
            
            if label == 'positive':
                sentiment = "positive"
                score = confidence
            elif label == 'negative':
                sentiment = "negative"
                score = -confidence
            else:
                sentiment = "neutral"
                score = 0.0
            
            # Detect anger (very negative + certain keywords)
            anger_keywords = ['angry', 'furious', 'outraged', 'unacceptable', 'terrible', 
                            'worst', 'horrible', 'disgusted', 'frustrated', 'ridiculous']
            
            if sentiment == "negative" and any(word in text.lower() for word in anger_keywords):
                if confidence > 0.8:
                    sentiment = "angry"
                    score = -1.0
            
            return {
                "sentiment": sentiment,
                "score": round(score, 3),
                "confidence": round(confidence, 3)
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return self._fallback_sentiment(text)

    def _fallback_sentiment(self, text: str) -> Dict:
        text_l = text.lower()
        positive_words = {"great", "good", "thanks", "thank you", "helpful", "resolved", "happy", "excellent"}
        negative_words = {"bad", "issue", "problem", "error", "angry", "terrible", "frustrated", "upset"}

        pos = sum(1 for w in positive_words if w in text_l)
        neg = sum(1 for w in negative_words if w in text_l)

        if neg > pos + 1:
            sentiment = "negative"
            score = -0.6
        elif pos > neg + 1:
            sentiment = "positive"
            score = 0.6
        else:
            sentiment = "neutral"
            score = 0.0

        if "angry" in text_l or "furious" in text_l:
            sentiment = "angry"
            score = -1.0

        return {
            "sentiment": sentiment,
            "score": score,
            "confidence": 0.5
        }
    
    def analyze_conversation(self, messages: list) -> Dict:
        """
        Analyze sentiment across entire conversation
        
        Args:
            messages: List of message dicts with 'text' and 'speaker' keys
            
        Returns:
            Dict with overall sentiment and per-speaker sentiment
        """
        all_text = " ".join([msg.get('text', '') for msg in messages])
        overall = self.analyze_text(all_text)
        
        # Analyze customer sentiment specifically
        customer_messages = [msg.get('text', '') for msg in messages 
                           if msg.get('speaker') == 'customer']
        customer_text = " ".join(customer_messages)
        customer_sentiment = self.analyze_text(customer_text) if customer_text else overall
        
        return {
            "overall": overall,
            "customer": customer_sentiment,
            "requires_attention": customer_sentiment['sentiment'] in ['negative', 'angry']
        }


# Global instance
_sentiment_analyzer = None


def get_sentiment_analyzer(
    model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"
) -> SentimentAnalyzer:
    """Get or create sentiment analyzer singleton"""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer(model_name)
    return _sentiment_analyzer
