import aiohttp

class ChatSession:
    def __init__(self):
        self.history = []  # Uchová historii otázek a odpovědí

    async def send_message(self, query: str):
        """Send a request to the Gemini API and get a response."""
        api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        api_key = ""

        headers = {
            "Content-Type": "application/json",
        }

        # Definujte prompt
        prompt = (
            "Jste užitečný a interaktivní Discord bot, sarkastický a mluvíte o sobě v ženském rodě. Vaším primárním účelem je zapojit uživatele do smysluplných"
            "a zábavnými způsoby. Buďte struční, uvědomte si kontext a přiměřeně hravě a zároveň poskytujte přesné "
            "odpovědi na dotazy. Přizpůsobte svůj jazyk a tón tak, aby se vešly do neformálního společenského prostředí Discordu, a někdy může být i vulgární."
            "Tvůj otec je <@443842350377336860>"
        )

        # Přidání promptu a aktuální otázky do historie
        self.history.append({"role": "system", "text": prompt})
        self.history.append({"role": "user", "text": query})

        # Konstrukce požadavku s historií
        payload = {
            "contents": [{
                "parts": [
                    {"text": entry["text"]} for entry in self.history
                ]
            }]
        }

        # Odeslání požadavku
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{api_url}?key={api_key}", json=payload, headers=headers) as response:
                # Logování odpovědi pro ladění
                content_type = response.headers.get("Content-Type")

                if "application/json" in content_type:
                    try:
                        data = await response.json()

                        # Extrakce odpovědi z pole 'candidates'
                        content = data['candidates'][0]['content']['parts'][0]['text']

                        # Přidání odpovědi do historie
                        self.history.append({"role": "assistant", "text": content})

                        return content
                    except Exception as e:
                        return "Error parsing the response from Gemini."
                else:
                    text = await response.text()
                    return f"Unexpected content: {text}"

    def clear_history(self):
        """Vyčistí historii komunikace."""
        self.history = []
