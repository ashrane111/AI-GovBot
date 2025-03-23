from main.config_loader import config_loader
from main.llm_clients.client_factory import create_llm_client

class Generator:
    def __init__(self):
        # Load provider and token from config
        self.client = create_llm_client(config_loader.get("llm.client", "huggingface"))
        self.messages = []

    async def generate(self, context, query):
        # Combine context and query into a single prompt, truncating context if too long
        prompt = f"Context: {context[:500]}...\nQuery: {query}\nAnswer:"
        prompt_message = {"role": "user", "content": prompt}
        self.messages.append(prompt_message)
        
        try:
            content = await self.client.generate_completion(self.messages)
        except Exception as e:
            print(f"Error generating response: {e}")
            content = "Fallback: Unable to generate response."
        
        assistant_prompt = {"role": "assistant", "content": content}
        self.messages.append(assistant_prompt)
            
        return {"content": content, "messages": self.messages}