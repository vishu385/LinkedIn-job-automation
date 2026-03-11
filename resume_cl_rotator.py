"""
LLM Hub Wrapper for Resume/Cover Letter Generation
- Loads configuration from .docs.env
- Uses UnifiedRotator from llm_hub.py
"""
import os
from dotenv import load_dotenv
from llm_hub import UnifiedRotator

class UniversalDocRotator:
    def __init__(self, rotation_limit=3, state_file=".llm_docs_state.json"):
        """
        Initialize Universal LLM rotator for document generation.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        docs_env_path = os.path.join(current_dir, '.docs.env')
        
        if os.path.exists(docs_env_path):
            print(f"📖 Loading config from: .docs.env")
            load_dotenv(dotenv_path=docs_env_path, override=True)
        else:
            print(f"⚠️ .docs.env not found, using default .env")
            env_path = os.path.join(current_dir, '.env')
            load_dotenv(dotenv_path=env_path, override=True)
        
        # Parse API keys and rotation limit
        llm_keys = os.getenv("LLM_API_KEYS", "")
        if not llm_keys:
            print("❌ Error: No LLM_API_KEYS found in .docs.env")
            llm_keys = "DUMMY_KEY"
            
        env_limit = os.getenv("LLM_ROTATION_LIMIT")
        self.rotation_limit = int(env_limit) if env_limit else rotation_limit
        self.model_override = os.getenv("LLM_MODEL_OVERRIDE")

        # Initialize Hub Rotator
        self.hub = UnifiedRotator(
            llm_keys, 
            limit=self.rotation_limit, 
            state_file=state_file
        )
        
        print(f"🎯 Universal Doc Rotator: Initialized (Limit: {self.rotation_limit})")

    def generate(self, prompt, model_name=None):
        """
        Generate content using the unified hub.
        """
        system_prompt = "You are a professional resume and cover letter writer."
        # Use override if set, else use passed model_name
        final_model = self.model_override or model_name
        
        # We need a small adjustment to llm_hub to support model_name per-call if needed,
        # but for now we'll use the hub's internal logic.
        return self.hub.generate(system_prompt, prompt)

# Global instance compatibility
_rotator = None
def get_rotator():
    global _rotator
    if _rotator is None:
        _rotator = UniversalDocRotator()
    return _rotator

if __name__ == "__main__":
    print("\n=== Testing UniversalDocRotator ===\n")
    rotator = get_rotator()
    try:
        result = rotator.generate("Say 'Universal test successful!' in one line.")
        print(f"\n📝 Response: {result}")
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    # Test rotation
    print("\n=== Testing Gemini Rotator ===\n")
    
    rotator = get_rotator()
    
    test_prompt = "Say 'Hello, rotation test successful!' in one line."
    
    try:
        result = rotator.generate(test_prompt)
        print(f"\n📝 Response: {result}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
