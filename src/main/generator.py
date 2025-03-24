from main.config_loader import config_loader
from main.llm_clients.client_factory import create_llm_client

class Generator:
    def __init__(self):
        # Load provider and token from config
        self.client = create_llm_client(config_loader.get("llm.client", "openai"))
        # self.messages = []

    async def generate(self, query_message):        
        try:
            content = await self.client.generate_completion(query_message)
        except Exception as e:
            print(f"Error generating response: {e}")
            content = "Fallback: Unable to generate response."
        
        assistant_prompt = {"role": "assistant", "content": content}
        query_message.append(assistant_prompt)
            
        return {"content": content, "messages": query_message}