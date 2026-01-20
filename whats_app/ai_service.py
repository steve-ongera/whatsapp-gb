# ai_service.py - Claude AI Integration
import anthropic
import os
from django.conf import settings
import json

class ClaudeAIService:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
        self.model = "claude-sonnet-4-20250514"
    
    def generate_text_response(self, user_message, conversation_history=None):
        """Generate text response from Claude AI"""
        messages = []
        
        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": "user" if msg.is_user else "assistant",
                    "content": msg.content
                })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system="You are a helpful AI assistant integrated into WhatsApp. You're friendly, conversational, and help users with anything they need - from answering questions to having casual conversations. Keep responses concise and natural, like texting a friend.",
                messages=messages
            )
            
            return response.content[0].text
        
        except Exception as e:
            print(f"Claude AI Error: {e}")
            return "Sorry, I'm having trouble responding right now. Please try again later."
    
    def generate_voice_response(self, user_message, conversation_history=None):
        """Generate voice response - first get text, then convert to speech"""
        text_response = self.generate_text_response(user_message, conversation_history)
        
        # Here you would integrate with a text-to-speech service
        # For example, using Google Cloud Text-to-Speech, Amazon Polly, etc.
        
        return {
            'text': text_response,
            'audio_url': None  # Would be the URL to the generated audio file
        }
    
    def handle_boredom_detection(self, message):
        """Detect if user is bored and offer to chat"""
        boredom_keywords = ['bored', 'boring', 'nothing to do', 'tired', 'lonely']
        
        message_lower = message.lower()
        is_bored = any(keyword in message_lower for keyword in boredom_keywords)
        
        if is_bored:
            return True, "I noticed you might be feeling bored! Would you like to chat with me? I can answer questions, tell jokes, discuss interesting topics, or just have a friendly conversation. What sounds good to you?"
        
        return False, None

