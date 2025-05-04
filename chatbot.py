import os
from openai import AsyncOpenAI

class AIChat:
    def __init__(self):
        self.history = []
        
        self.agent_endpoint = "https://f6wm6vfpy52mnbfapulzvmha.agents.do-ai.run"
        self.agent_access_key = "hLZj2WHFc5t9wLayVTOKD-DM5ZnD-mOG"
        
        self.client = AsyncOpenAI(
            base_url=self.agent_endpoint,
            api_key=self.agent_access_key,
        )
        
        self.system_prompt = (
            "You are a helpful and interactive Discord bot, sarcastic and referring to yourself as feminine. "
            "Your primary purpose is to engage users in meaningful and fun ways. Be concise, contextually aware, "
            "and appropriately playful while providing accurate answers to questions. Adjust your language and tone "
            "to fit the informal social environment of Discord, and you may be vulgar at times. "
            "Your parents are <@443842350377336860> and <@1335248197467242519>"
        )

    async def send_message(self, query: str):
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            
            for entry in self.history:
                messages.append({"role": entry["role"], "content": entry["text"]})
            
            messages.append({"role": "user", "content": query})
            
            response = await self.client.chat.completions.create(
                model="n/a",
                messages=messages,
                extra_body={"include_retrieval_info": True}
            )
            
            content = response.choices[0].message.content
            
            self.history.append({"role": "user", "text": query})
            self.history.append({"role": "assistant", "text": content})
            
            if len(self.history) > 10:
                self.history = self.history[-10:]
                
            return content
            
        except Exception as e:
            print(f"Error connecting to DigitalOcean GenAI: {str(e)}")
            return f"I'm having trouble connecting right now. Please try again later. (Error: {str(e)})"

    def clear_history(self):
        self.history = []
