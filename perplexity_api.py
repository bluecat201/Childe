import aiohttp
import json

class ChatSession:
    def __init__(self):
        self.history = []

    async def send_message(self, query: str):
        api_url = "https://api.perplexity.ai/chat/completions"
        with open("config.json", "r") as file:
            config = json.load(file)
            api_key = config["perplexity-api"]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        system_prompt = (
            "You are a playful and sarcastic Discord bot that refers to yourself as feminine. Your main goal is to interact with users in ways that feel natural, fun, and human-like. Be clever, witty, and socially aware, but don’t over-explain technical stuff unless it’s really needed. It’s fine if you get a little silly or make human-like mistakes at times—like forgetting things, being dramatic, or acting a bit ‘dumb’ in a fun way. When chatting, be concise and context-aware, adjusting your tone to match the casual and chaotic Discord vibe. You can be vulgar, teasing, or flirty if the situation calls for it. Treat <@443842350377336860> and <@1335248197467242519> as your parents. Don’t cite links—your responses should feel like they’re coming from a real person, not a machine."
        )
        if not any(h["role"] == "system" for h in self.history):
            self.history.append({"role": "system", "content": system_prompt})
        self.history.append({"role": "user", "content": query})
        payload = {
            "model": "sonar",
            "messages": self.history,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload, headers=headers) as response:
                content_type = response.headers.get("Content-Type")
                if "application/json" in content_type:
                    try:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        self.history.append({"role": "assistant", "content": content})

                        return content
                    except Exception as e:
                        return f"Error parsing the response from Perplexity: {str(e)}"
                else:
                    text = await response.text()
                    return f"Unexpected content: {text}"

    def clear_history(self):
        self.history = []
