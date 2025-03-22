from huggingface_hub import InferenceClient
from main.config_loader import config_loader

class Generator:
    def __init__(self):
        # Load provider and token from config
        provider = config_loader.get("novita.provider", "novita")
        token = config_loader.get("novita.token")
        self.client = InferenceClient(provider=provider, token=token)

    def generate(self, context, query):
        # Combine context and query into a single prompt, truncating context if too long
        prompt = f"Context: {context[:500]}...\nQuery: {query}\nAnswer:"
        try:
            completion = self.client.chat.completions.create(
                model="deepseek-ai/DeepSeek-R1",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,  # Increased from 100 to match your provided code
                temperature=0.7,
                top_p=0.9,
            )
            content = completion.choices[0].message["content"]
        except Exception as e:
            print(f"Error with Inference API: {e}")
            content = "Fallback: Unable to generate response."
        return {"content": content}