import requests
import json
from src.utils import setup_logging

logger = setup_logging()

class BrainClient:
    def __init__(self, config):
        self.config = config
        self.webhook_url = config.get("n8n_webhook_url")
        self.output_schema_keys = {"category", "confidence", "suggested_name", "folder", "tags"}

    def ask_brain(self, file_context):
        if not self.webhook_url:
            logger.error("No n8n Webhook URL configured.")
            return None

        try:
            logger.info(f"Sending context to Brain: {file_context.get('filename')}")
            response = requests.post(self.webhook_url, json=file_context, timeout=10)
            response.raise_for_status()
            
            try:
                data = response.json()
                
                # Handle raw OpenAI structure if n8n passes it through directly
                if "message" in data and "content" in data["message"]:
                    try:
                        content_str = data["message"]["content"]
                        # Clean markdown code blocks if present
                        content_str = content_str.replace("```json", "").replace("```", "").strip()
                        data = json.loads(content_str)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse inner JSON from OpenAI message: {data['message']['content']}")
                        return None
                        
            except ValueError:
                logger.error(f"Brain returned non-JSON response. Status: {response.status_code}. Body: {response.text[:200]}")
                return None

            if self._validate_response(data):
                return data
            else:
                logger.warning(f"Invalid response from Brain: {data}")
                return None
        except Exception as e:
            logger.error(f"Brain request failed: {e}")
            return None

    def _validate_response(self, data):
        # Strict validation of Output Contract
        if not isinstance(data, dict):
            return False
        
        # Check required keys
        if not self.output_schema_keys.issubset(data.keys()):
            logger.warning(f"Missing keys in brain response. Expected {self.output_schema_keys}, got {data.keys()}")
            return False

        # Type checks
        if not isinstance(data.get("confidence"), (int, float)):
             return False
        
        if not isinstance(data.get("tags"), list):
             return False

        return True
