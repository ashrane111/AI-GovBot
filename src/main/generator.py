import requests
from .config_loader import config_loader

class Generator:
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf"
        self.api_token = config_loader.get("huggingface.hf_token")
        self.headers = {"Authorization": f"Bearer {self.api_token}"}

    def generate(self, context, query):
        # Truncate context to ~500 characters to stay within token limits
        truncated_context = context[:500] + "..." if len(context) > 500 else context
        prompt = f"Context: {truncated_context}\nQuery: {query}\nAnswer:"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 100,
                "temperature": 0.7,
                "top_p": 0.9,
                "return_full_text": False
            }
        }
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            content = response.json()[0]["generated_text"]
        except requests.exceptions.RequestException as e:
            error_msg = f"Error with Inference API: {str(e)}"
            if hasattr(e.response, 'text'):
                error_msg += f" - Details: {e.response.text}"
            print(error_msg)
            content = "Fallback: Unable to generate response."
        return {"content": content}