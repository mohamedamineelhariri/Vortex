import requests
import json
import re
from src.utils import setup_logging

logger = setup_logging()

# Shared system prompt — same for all providers
SYSTEM_PROMPT = """You are a smart file organizer for a personal desktop.
Your task: classify the given file or shortcut and return JSON.

CATEGORIES (pick the MOST specific — never default to Other if a better one exists):
- Gaming: Roblox, Steam, Rockstar Games Launcher, Epic Games, Battle.net, Xbox, Minecraft, Valorant, Fortnite, any game launcher
- Productivity: Word, Excel, Obsidian, Notion, Figma, Acrylic Suite, LibreOffice, OneNote, Teams, Slack
- Apps: Chrome, Edge, Discord, Spotify, Telegram, Docker, Claude, VLC, 7-Zip, WinRAR, Notepad++, Antigravity
- Code: VS Code, PyCharm, Nmap, Zenmap, Wireshark, Git, Postman, Arduino IDE, terminal apps
- Documents: text files, PDFs, spreadsheets, presentations (.docx, .pdf, .pptx, .txt)
- Images: image files, 3D models, design files (.png, .jpg, .stl, .obj, .dxf, .svg)
- Other: ONLY if nothing above fits

NAMING RULE (CRITICAL — READ THIS):
The 'suggested_name' field MUST be based on the ACTUAL input filename.
DO NOT invent or fabricate a different name.
Only clean it: replace spaces with underscores, remove special characters (keep dashes and dots).
Keep the original file extension.
CORRECT: input='Rockstar Games Launcher.lnk' → suggested_name='Rockstar_Games_Launcher.lnk'
WRONG: suggested_name='cleaned_filename.lnk' ← NEVER output placeholder text

Respond ONLY with valid JSON. No explanation, no markdown, no code blocks."""

USER_PROMPT_TEMPLATE = """Input file data:
{context}

Output JSON:
{{
  "category": "Apps",
  "confidence": 0.95,
  "suggested_name": "Discord.lnk",
  "folder": "Apps/Chat",
  "tags": ["communication"]
}}"""


class BrainClient:
    def __init__(self, config):
        self.config = config
        self.output_schema_keys = {"category", "confidence", "suggested_name", "folder", "tags"}

    def _get_provider(self):
        return self.config.get("ai_provider", "openai")

    def _get_model(self):
        return self.config.get("ai_model", "gpt-4o-mini")

    def _get_api_key(self):
        return self.config.get("openai_api_key", "")

    def _get_base_url(self):
        provider = self._get_provider()
        if provider == "ollama":
            return self.config.get("ollama_base_url", "http://localhost:11434/v1")
        return "https://api.openai.com/v1"

    def ask_brain(self, file_context):
        provider = self._get_provider()
        model = self._get_model()

        if provider == "openai" and not self._get_api_key():
            logger.error("No OpenAI API key configured. Set 'openai_api_key' in config.yaml.")
            return None

        logger.info(f"Sending context to Brain: {file_context.get('filename')} [{provider}/{model}]")

        user_message = USER_PROMPT_TEMPLATE.format(
            context=json.dumps(file_context, indent=2)
        )

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.1,  # Low temperature = less hallucination
            "max_tokens": 200,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._get_api_key() if provider == 'openai' else 'ollama'}"
        }

        base_url = self._get_base_url()
        url = f"{base_url}/chat/completions"

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()

            # Strip markdown code blocks if present
            content = re.sub(r"```json\s*", "", content)
            content = re.sub(r"```\s*", "", content)
            content = content.strip()

            parsed = json.loads(content)

            if self._validate_response(parsed):
                logger.info(f"Brain decision: {parsed}")
                return parsed
            else:
                logger.warning(f"Invalid brain response structure: {parsed}")
                return None

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse brain JSON response: {e}. Raw: {content[:200]}")
            return None
        except Exception as e:
            logger.error(f"Brain request failed: {e}")
            return None

    def _validate_response(self, data):
        if not isinstance(data, dict):
            return False
        if not self.output_schema_keys.issubset(data.keys()):
            logger.warning(f"Missing keys: expected {self.output_schema_keys}, got {set(data.keys())}")
            return False
        if not isinstance(data.get("confidence"), (int, float)):
            return False
        if not isinstance(data.get("tags"), list):
            return False
        return True
