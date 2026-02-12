import httpx
import os
from typing import Dict, List
import logging
import json

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """Generate AI summaries of call transcripts"""
    
    def __init__(self, api_key: str = None, use_local: bool = False):
        """
        Initialize summary generator
        
        Args:
            api_key: OpenAI API key (optional)
            use_local: Use local summarization instead of API
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.use_local = use_local or not self.api_key
        
        if self.use_local:
            logger.info("Using rule-based summarization (no API key)")
        else:
            logger.info("Using OpenAI API for summarization")
    
    async def generate_summary(self, transcript: str, context: Dict = None) -> Dict:
        """
        Generate call summary
        
        Args:
            transcript: Full call transcript
            context: Additional context (agent name, customer info, etc.)
            
        Returns:
            Dict with summary, key_points, intent, and action_items
        """
        if self.use_local:
            return self._generate_rule_based_summary(transcript, context)
        else:
            return await self._generate_ai_summary(transcript, context)
    
    def _generate_rule_based_summary(self, transcript: str, context: Dict = None) -> Dict:
        """
        Generate summary using rules and keyword extraction
        """
        lines = [line.strip() for line in transcript.split('\n') if line.strip()]
        
        # Extract key sentences (simple heuristic)
        key_points = []
        for line in lines[:5]:  # First 5 lines often contain key info
            if len(line) > 20 and any(word in line.lower() for word in 
                                     ['need', 'want', 'issue', 'problem', 'help', 'question']):
                key_points.append(line)
        
        # Detect intent
        intent_keywords = {
            'inquiry': ['question', 'ask', 'wondering', 'curious', 'information'],
            'complaint': ['problem', 'issue', 'wrong', 'not working', 'broken', 'error'],
            'request': ['need', 'want', 'would like', 'request', 'help'],
            'feedback': ['feedback', 'suggestion', 'think', 'recommend'],
        }
        
        detected_intent = "general_inquiry"
        for intent, keywords in intent_keywords.items():
            if any(keyword in transcript.lower() for keyword in keywords):
                detected_intent = intent
                break
        
        # Generate simple summary
        summary = f"Call regarding {detected_intent}. "
        if len(lines) > 0:
            summary += f"Customer mentioned: {lines[0][:100]}..."
        
        # Extract action items (sentences with should, will, need to)
        action_items = []
        action_words = ['will', 'should', 'need to', 'follow up', 'send', 'provide']
        for line in lines:
            if any(word in line.lower() for word in action_words):
                action_items.append(line)
        
        return {
            "summary": summary,
            "key_points": key_points[:3],
            "customer_intent": detected_intent,
            "action_items": action_items[:3]
        }
    
    async def _generate_ai_summary(self, transcript: str, context: Dict = None) -> Dict:
        """
        Generate summary using OpenAI API
        """
        try:
            prompt = f"""Analyze this call transcript and provide:
1. A brief summary (2-3 sentences)
2. Key discussion points (3-5 bullet points)
3. Customer's primary intent
4. Action items or next steps

Transcript:
{transcript[:2000]}  # Limit length

Respond in JSON format:
{{
    "summary": "...",
    "key_points": ["...", "..."],
    "customer_intent": "...",
    "action_items": ["...", "..."]
}}
"""
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {"role": "system", "content": "You are a call analysis assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 500
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    
                    # Parse JSON response
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        # Fallback if response isn't valid JSON
                        return {
                            "summary": content[:200],
                            "key_points": [],
                            "customer_intent": "general_inquiry",
                            "action_items": []
                        }
                else:
                    logger.error(f"API error: {response.status_code}")
                    return self._generate_rule_based_summary(transcript, context)
                    
        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            return self._generate_rule_based_summary(transcript, context)


# Global instance
_summary_generator = None


def get_summary_generator(api_key: str = None) -> SummaryGenerator:
    """Get or create summary generator singleton"""
    global _summary_generator
    if _summary_generator is None:
        _summary_generator = SummaryGenerator(api_key)
    return _summary_generator
