import os
from src.utils.logger import logger
from src.config.bot_config import GEMINI_API_KEY

try:
    from google import genai
    from google.genai import types, errors
except ImportError:
    raise ImportError("Please install google-genai: pip install google-genai")

# Read model name from environment variable, fallback to a default
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

class GeminiLLM:
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model or GEMINI_MODEL
        # The SDK will pick up GEMINI_API_KEY from env automatically
        self.client = genai.Client()
        logger.info(f"Initialized GeminiLLM with model: {self.model}")

    def chat(self, prompt, system_instruction=None):
        logger.info("Sending prompt to Gemini")
        config = None
        if system_instruction:
            config = types.GenerateContentConfig(system_instruction=system_instruction)
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt],
                config=config
            )
            logger.info("Gemini responded back")
            return response.text
        except errors.APIError as e:
            logger.error(f"Gemini API error: {e.code} - {e.message}")
            return f"[Gemini API error: {e.code} - {e.message}]"
        except Exception as e:
            logger.exception(f"Exception during Gemini API call: {e}")
            return f"[Gemini Exception: {e}]" 