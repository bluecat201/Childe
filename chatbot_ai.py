"""
AI Chatbot API Implementation for Discord Bot
Uses the sidet.eu AI API with personalized tokens and conversation memory
"""

import aiohttp
import json
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

class ChatbotAPI:
    """
    AI Chatbot API client that integrates with sidet.eu API
    Maintains conversation history and provides personalized AI responses
    """
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the chatbot API client"""
        self.api_url = "https://api.sidet.eu/ai_api.php"
        self.config_path = config_path
        self.token = None
        self.model = "gemini-2.5-flash"  # Default model
        self.history = []  # Local conversation history for context
        self.max_history = 10  # Keep last 10 conversations for context
        
        # Load configuration
        self._load_config()
    
    def _load_config(self):
        """Load configuration from config.json"""
        try:
            with open(self.config_path, "r") as file:
                config = json.load(file)
                # Get AI API token from config
                self.token = config.get("ai_api", {}).get("token", "test123")  # Default to test123
                self.model = config.get("ai_api", {}).get("default_model", "gemini-2.5-flash")
        except Exception as e:
            print(f"Error loading config: {e}")
            # Use default values
            self.token = "test123"
            self.model = "gemini-2.5-flash"
    
    async def send_message(self, prompt: str, model: Optional[str] = None, user_context: Optional[Dict] = None) -> str:
        """
        Send a message to the AI API and get a response
        
        Args:
            prompt: The user's message/question
            model: Optional model override
            user_context: Optional user context for personalization
            
        Returns:
            AI response string
        """
        if not prompt.strip():
            return "I need a message to respond to!"
        
        # Use provided model or default
        selected_model = model or self.model
        
        # Add user context to prompt if provided
        contextualized_prompt = self._add_context_to_prompt(prompt, user_context)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"sideteu {self.token}"
        }
        
        payload = {
            "prompt": contextualized_prompt,
            "model": selected_model
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("success"):
                            ai_response = data["response"]
                            
                            # Add to local history
                            self._add_to_history(prompt, ai_response)
                            
                            return ai_response
                        else:
                            error_msg = data.get("error", "Unknown error")
                            print(f"API Error: {error_msg}")
                            return f"API Error: {error_msg}"
                    
                    elif response.status == 401:
                        return "Authentication failed - invalid token"
                    
                    elif response.status == 400:
                        return "Bad request - check your message format"
                    
                    else:
                        error_text = await response.text()
                        print(f"HTTP {response.status}: {error_text}")
                        return f"Service temporarily unavailable (HTTP {response.status})"
        
        except aiohttp.ClientError as e:
            print(f"Network error: {e}")
            return "Network error - please try again later"
        
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return "Invalid response format from API"
        
        except Exception as e:
            print(f"Unexpected error: {e}")
            return "An unexpected error occurred"
    
    def _add_context_to_prompt(self, prompt: str, user_context: Optional[Dict] = None) -> str:
        """
        Add conversation history and user context to the prompt
        """
        contextualized_prompt = prompt
        
        # Add user context if provided
        if user_context:
            context_info = []
            if user_context.get("username"):
                context_info.append(f"User: {user_context['username']}")
            if user_context.get("guild_name"):
                context_info.append(f"Server: {user_context['guild_name']}")
            if user_context.get("channel_name"):
                context_info.append(f"Channel: #{user_context['channel_name']}")
            
            if context_info:
                context_str = " | ".join(context_info)
                contextualized_prompt = f"[Context: {context_str}]\n{prompt}"
        
        # The API handles conversation history automatically per token,
        # but we keep local history for potential fallback or additional context
        return contextualized_prompt
    
    def _add_to_history(self, prompt: str, response: str):
        """Add interaction to local history"""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response
        })
        
        # Keep only last N interactions
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.history.copy()
    
    def clear_history(self):
        """Clear local conversation history"""
        self.history = []
    
    def set_model(self, model: str):
        """Change the AI model"""
        valid_models = [
            "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash",
            "gemini-flash", "gemini-pro"
        ]
        
        if model in valid_models:
            self.model = model
            return True
        return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return [
            "gemini-2.5-flash",  # Latest fast model (default)
            "gemini-2.5-pro",   # Latest pro model
            "gemini-2.0-flash", # Previous generation fast
            "gemini-flash",     # Alias for 2.5-flash
            "gemini-pro"        # Alias for 2.5-pro
        ]
    
    def get_model_info(self, model: str) -> Dict[str, str]:
        """Get information about a specific model"""
        model_info = {
            "gemini-2.5-flash": {
                "description": "Latest fast model (default)",
                "speed": "⚡ Fastest",
                "capability": "Good for most tasks"
            },
            "gemini-2.5-pro": {
                "description": "Latest pro model",
                "speed": "🐌 Slower",
                "capability": "Best reasoning & complex tasks"
            },
            "gemini-2.0-flash": {
                "description": "Previous generation fast",
                "speed": "⚡ Fast",
                "capability": "Alternative option"
            },
            "gemini-flash": {
                "description": "Alias for 2.5-flash",
                "speed": "⚡ Fastest",
                "capability": "Same as gemini-2.5-flash"
            },
            "gemini-pro": {
                "description": "Alias for 2.5-pro",
                "speed": "🐌 Slower",
                "capability": "Same as gemini-2.5-pro"
            }
        }
        
        return model_info.get(model, {"description": "Unknown model", "speed": "Unknown", "capability": "Unknown"})
    
    def get_current_token_personality(self) -> str:
        """Get information about current token's personality"""
        personalities = {
            "test123": "Alex - Friendly and enthusiastic AI assistant with casual, upbeat tone",
            "demo456": "Professor Minerva - Wise and scholarly AI assistant with formal, academic tone",
            "admin789": "Codex - Technical AI assistant with concise, practical tone focused on programming"
        }
        
        return personalities.get(self.token, f"Unknown personality for token: {self.token}")
    
    def set_token(self, token: str):
        """Change the API token (and thus personality)"""
        self.token = token
        # Clear history when changing tokens since each token has separate conversation memory
        self.clear_history()


class ChatSession:
    """
    Legacy compatibility class for existing code
    Wraps the new ChatbotAPI for backward compatibility
    """
    
    def __init__(self):
        self.api = ChatbotAPI()
        self.history = []  # Keep for compatibility
    
    async def send_message(self, query: str) -> str:
        """Send message using the new API (compatibility method)"""
        response = await self.api.send_message(query)
        
        # Keep local history for compatibility
        self.history.append({"role": "user", "text": query})
        self.history.append({"role": "assistant", "text": response})
        
        return response
    
    def clear_history(self):
        """Clear history (compatibility method)"""
        self.history = []
        self.api.clear_history()


# Example usage and testing
async def test_chatbot():
    """Test function to verify the chatbot works"""
    chatbot = ChatbotAPI()
    
    print(f"Using token: {chatbot.token}")
    print(f"Personality: {chatbot.get_current_token_personality()}")
    print(f"Model: {chatbot.model}")
    print()
    
    # Test basic conversation
    response = await chatbot.send_message("Hello! How are you today?")
    print(f"AI: {response}")
    print()
    
    # Test with user context
    user_context = {
        "username": "TestUser",
        "guild_name": "Test Server",
        "channel_name": "general"
    }
    
    response = await chatbot.send_message("What's my name?", user_context=user_context)
    print(f"AI: {response}")
    print()
    
    # Test model change
    print("Available models:", chatbot.get_available_models())
    chatbot.set_model("gemini-2.5-pro")
    print(f"Changed to model: {chatbot.model}")
    
    response = await chatbot.send_message("Explain quantum physics briefly")
    print(f"AI (Pro model): {response}")


if __name__ == "__main__":
    # Run test if this file is executed directly
    asyncio.run(test_chatbot())
