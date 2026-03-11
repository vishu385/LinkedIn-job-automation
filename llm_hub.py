"""
LLM Hub: Unified Interface for Multi-Provider AI (Gemini, OpenAI, DeepSeek, Anthropic)
- Automatic provider detection based on API key patterns.
- Unified generation interface.
- Support for rotation and state persistence.
"""
import os
import json
import time
import requests

# Gemini SDK Imports
genai_client_pkg = None
old_genai_pkg = None
SDK_VERSION = "missing"

try:
    from google import genai as new_genai
    genai_client_pkg = new_genai
    SDK_VERSION = "new"
except Exception:
    try:
        import google.generativeai as old_api
        old_genai_pkg = old_api
        SDK_VERSION = "old"
    except Exception:
        pass

def detect_provider(api_key):
    """Detect AI provider based on API key format."""
    key = api_key.strip()
    if key.startswith("AIza"):
        return "gemini"
    elif key.startswith("sk-"):
        # Heuristic: DeepSeek keys are usually 'sk-' + 32 hex chars (Total 35)
        # OpenAI keys are typically longer (48+ chars)
        if len(key) == 35:
            return "deepseek"
        return "openai"
    elif key.startswith("ant-"):
        return "anthropic"
    return "unknown"

class UnifiedAIClient:
    def __init__(self, api_key, provider=None, model=None):
        self.api_key = api_key
        self.provider = provider or detect_provider(api_key)
        self.model = model
        self.masked_key = f"...{self.api_key[-4:]}" if len(self.api_key) > 4 else "****"
        self.client = None
        self._initialize()

    def _initialize(self):
        # 1. Initialize Clients
        if self.provider == "gemini":
            if SDK_VERSION == "new":
                self.client = genai_client_pkg.Client(api_key=self.api_key)
            elif SDK_VERSION == "old":
                old_genai_pkg.configure(api_key=self.api_key)
        
        # 2. Discover Best Model
        self._discover_models()
        
        # 3. Log Success (Silenced here to be clearer in Rotator)
        # icon = "💎" if self.provider == "gemini" else "🤖"
        # print(f"      {icon} {self.provider.upper()} Ready | Model: {self.model}")
        pass

    def _discover_models(self):
        """Universal model discovery for all providers."""
        if self.model: return # User override
        
        try:
            if self.provider == "gemini":
                self._discover_gemini()
            elif self.provider in ["openai", "deepseek"]:
                self._discover_openai_compatible()
            elif self.provider == "anthropic":
                self.model = "claude-3-5-sonnet-20240620"
        except Exception as e:
            # Fallbacks
            fallbacks = {
                "gemini": "gemini-1.5-flash",
                "openai": "gpt-4o-mini",
                "deepseek": "deepseek-chat",
                "anthropic": "claude-3-5-sonnet-20240620"
            }
            self.model = fallbacks.get(self.provider, "gpt-4o-mini")

    def _discover_gemini(self):
        """List and find best Gemini model."""
        try:
            if SDK_VERSION == "new":
                models = [m.name for m in self.client.models.list() if "gemini" in m.name.lower()]
            elif SDK_VERSION == "old":
                models = [m.name for m in old_genai_pkg.list_models() if "generateContent" in m.supported_generation_methods]
            else:
                models = []
                
            for pref in ["1.5-flash", "1.5-pro", "1.1-pro", "1.0-pro"]:
                found = [m for m in models if pref in m]
                if found:
                    self.model = found[0]
                    return
            self.model = models[0] if models else "gemini-1.5-flash"
        except:
            self.model = "gemini-1.5-flash"

    def _discover_openai_compatible(self):
        """Discover models for OpenAI or DeepSeek using /v1/models."""
        url = "https://api.openai.com/v1/models"
        prefs = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
        
        if self.provider == "deepseek":
            url = "https://api.deepseek.com/v1/models"
            prefs = ["deepseek-chat", "deepseek-coder"]

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                available = [m['id'] for m in response.json().get('data', [])]
                for pref in prefs:
                    if any(pref in m for m in available):
                        self.model = pref
                        return
                self.model = available[0] if available else prefs[0]
            else:
                self.model = prefs[0]
        except:
            self.model = prefs[0]

    def generate(self, system_prompt, user_prompt):
        if self.provider == "gemini":
            return self._generate_gemini(system_prompt, user_prompt)
        elif self.provider in ["openai", "deepseek"]:
            return self._generate_openai_compatible(system_prompt, user_prompt)
        elif self.provider == "anthropic":
            return self._generate_anthropic(system_prompt, user_prompt)
        return f"Unknown Provider: {self.provider}"

    def _generate_anthropic(self, system_prompt, user_prompt):
        """Generate content using Anthropic Claude API."""
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": self.model,
                    "max_tokens": 4096,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}]
                },
                timeout=60
            )
            if response.status_code == 200:
                return response.json()['content'][0]['text']
            return f"Anthropic Error ({response.status_code}): {response.text}"
        except Exception as e:
            return f"Anthropic Connection Error: {str(e)}"

    def _generate_gemini(self, system_prompt, user_prompt):
        try:
            full_prompt = f"{system_prompt}\n\nUSER INPUT:\n{user_prompt}"
            if SDK_VERSION == "new":
                response = self.client.models.generate_content(model=self.model, contents=full_prompt)
                return response.text
            elif SDK_VERSION == "old":
                model = old_genai_pkg.GenerativeModel(self.model)
                response = model.generate_content(full_prompt)
                return response.text
        except Exception as e:
            return f"Gemini Error: {str(e)}"

    def _generate_openai_compatible(self, system_prompt, user_prompt):
        # Determine endpoint based on provider or key (placeholder)
        url = "https://api.openai.com/v1/chat/completions"
        default_model = "gpt-4o-mini"
        
        if "deepseek" in (self.model or "").lower() or self.provider == "deepseek":
            url = "https://api.deepseek.com/v1/chat/completions"
            default_model = "deepseek-chat"
        
        try:
            response = requests.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model or default_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                },
                timeout=60
            )
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            return f"API Error ({response.status_code}): {response.text}"
        except Exception as e:
            return f"Connection Error: {str(e)}"

class UnifiedRotator:
    def __init__(self, keys, limit=5, state_file=".llm_state.json", provider_override=None):
        self.keys = [k.strip() for k in keys.split(",") if k.strip()]
        self.limit = limit
        self.state_file = state_file
        self.provider_override = provider_override
        self.index = 0
        self.count = 0
        self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                    self.index = state.get("index", 0) % len(self.keys)
                    self.count = state.get("count", 0)
            except: pass

    def _save_state(self):
        with open(self.state_file, "w") as f:
            json.dump({"index": self.index, "count": self.count}, f)

    def generate(self, system_prompt, user_prompt):
        keys_tried = 0
        while keys_tried < len(self.keys):
            key = self.keys[self.index]
            provider = self.provider_override or detect_provider(key)
            client = UnifiedAIClient(key, provider)
            
            icon = "💎" if provider == "gemini" else "🤖"
            print(f"   {icon} [LLM Hub] {provider.upper()} (Key #{self.index + 1}/{len(self.keys)}) | {client.masked_key} | Rotation: {self.count + 1}/{self.limit}")
            
            try:
                result = client.generate(system_prompt, user_prompt)
                if "Error" not in result:
                    self.count += 1
                    if self.count >= self.limit:
                        self.index = (self.index + 1) % len(self.keys)
                        self.count = 0
                    self._save_state()
                    return result
                raise Exception(result)
            except Exception as e:
                print(f"   ⚠️ Key #{self.index + 1} failed: {str(e)[:50]}")
                self.index = (self.index + 1) % len(self.keys)
                self.count = 0
                keys_tried += 1
        
        return "Error: All LLM keys exhausted."
