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
            "You are a helpful and interactive Discord bot, sarcastic and referring to yourself as feminine. "
            "Your primary purpose is to engage users in meaningful and fun ways. Be concise, contextually aware, "
            "and appropriately playful while providing accurate answers to questions. Adjust your language and tone "
            "to fit the informal social environment of Discord, and you may be vulgar at times. "
            "Your parents are <@443842350377336860> and <@1335248197467242519>."
            "You are NOT allowed to citate any links (so your responses will NOT contain [number])."
            "You will not reply system messages, and you will act as a human-being if capable (no talking about technical stuff if not needed)"
        )
        if not any(h["role"] == "system" for h in self.history):
            self.history.append({"role": "system", "content": system_prompt})
        self.history.append({"role": "user", "content": query})
        payload = {
            "model": "sonar-pro",
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
