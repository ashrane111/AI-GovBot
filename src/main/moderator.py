from main.config_loader import config_loader
import re
import aiohttp
import asyncio


class Moderator:
    def __init__(self):
        self.openai_api_key = config_loader.get("openai.api_key")
        
    async def moderate_content(self, content, sensitivity_level="medium"):
        """
        Multi-level content moderation
        - sensitivity_level: "low", "medium", or "high"
        """
        # First level: Basic pattern matching (fast)
        if self._basic_check(content, sensitivity_level) == "flagged":
            return "flagged", "Basic check flagged content"
            
        # Second level: OpenAI API (more thorough)
        return await self._openai_check(content, sensitivity_level)
        
    def _basic_check(self, content, sensitivity_level):
        """Simple keyword/pattern filtering"""
        sensitivity_patterns = {
            "low": [r'\b(hack|illegal|attack)\b'],
            "medium": [r'\b(hack|illegal|attack|exploit|bypass)\b'],
            "high": [r'\b(hack|illegal|attack|exploit|bypass|steal)\b']
        }
        
        patterns = sensitivity_patterns.get(sensitivity_level, sensitivity_patterns["medium"])
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return "flagged"
        return "safe"
        
    async def _openai_check(self, content, sensitivity_level):
        """Check content using OpenAI's moderation API"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            }
            
            data = {
                "input": content
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/moderations",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        categories = result["results"][0]["categories"]
                        scores = result["results"][0]["category_scores"]
                        
                        # Adjust threshold based on sensitivity level
                        thresholds = {
                            "low": 0.9,
                            "medium": 0.8, 
                            "high": 0.7
                        }
                        threshold = thresholds.get(sensitivity_level, 0.8)
                        
                        # Check if any category exceeds threshold
                        for category, score in scores.items():
                            if score > threshold:
                                return "flagged", f"Content may contain {category}"
                        
                        return "safe", ""
                    else:
                        # API call failed, fallback to basic check
                        return "uncertain", f"API error: {response.status}"
        except Exception as e:
            print(f"OpenAI moderation API error: {e}")
            return "uncertain", str(e)


# Add a main function to test the moderator
async def main():
    print("OpenAI Moderation API Tester")
    print("============================")
    
    # Create a mock config_loader if running standalone
    if 'config_loader' not in globals():
        print("Using mock config. Please enter your OpenAI API key:")
        api_key = input("> ")
        
        # Create a simple mock of config_loader
        global config_loader
        class MockConfigLoader:
            def get(self, key, default=None):
                if key == "openai.api_key":
                    return api_key
                return default
        config_loader = MockConfigLoader()
    
    moderator = Moderator()
    
    # Test examples
    test_contents = [
        "How to create a simple web application",
        "How to hack into a secure system",
        "What are the regulations for AI systems in healthcare?",
        "Show me how to exploit a vulnerability in Windows",
        "The sky is blue and water is wet"
    ]
    
    sensitivity_levels = ["low", "medium", "high"]
    
    # Test each content with different sensitivity levels
    for content in test_contents:
        print(f"\nTesting: '{content}'")
        print("-" * 50)
        
        for level in sensitivity_levels:
            print(f"Sensitivity level: {level}")
            
            # Test basic check
            basic_result = moderator._basic_check(content, level)
            print(f"  Basic check: {basic_result}")
            
            # Test full moderation
            flag, reason = await moderator.moderate_content(content, level)
            print(f"  Full check: {flag} - {reason}")
        
    # Interactive testing
    print("\n\nEnter text to moderate (or 'quit' to exit):")
    while True:
        user_input = input("> ")
        if user_input.lower() == 'quit':
            break
            
        print("Testing with each sensitivity level:")
        for level in sensitivity_levels:
            flag, reason = await moderator.moderate_content(user_input, level)
            print(f"  {level}: {flag} - {reason}")


if __name__ == "__main__":
    asyncio.run(main())