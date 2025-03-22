from abc import ABC, abstractmethod

class LLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    def generate_completion(self, prompt, max_tokens=500, temperature=0.7, top_p=0.9):
        """Generate a completion for the given prompt"""
        pass