from main.llm_clients.hugging_face_client import HuggingFaceClient
# Import other client types as needed

def create_llm_client(client_type):
    """Factory function to create the appropriate LLM client based on configuration"""
    match client_type:
        case "huggingface":
            return HuggingFaceClient()
        # Add other client types here
        case _:
            raise ValueError(f"Unsupported LLM client type: {client_type}")