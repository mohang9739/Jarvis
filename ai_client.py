import os
import json
from dotenv import load_dotenv
from google import genai as google_genai
from groq import Groq

load_dotenv()

# --- Configure both providers ---
gemini_client = google_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = "gemini-2.5-flash"

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = "openai/gpt-oss-20b"  # updated per Groq's Aug 16 2026 deprecation notice

def ask_ai(prompt: str, json_mode: bool = False) -> str:
    """
    Sends a prompt to Gemini (primary). Falls back to Groq automatically
    if Gemini fails or rate-limits. Returns raw text response.
    """
    if json_mode:
        prompt = prompt + "\n\nRespond ONLY with valid JSON, no markdown, no extra text."

    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        return response.text
    except Exception as gemini_error:
        print(f"[ai_client] Gemini failed, falling back to Groq: {gemini_error}")

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as groq_error:
        print(f"[ai_client] Groq also failed: {groq_error}")
        raise RuntimeError("Both Gemini and Groq failed to respond.")


def ask_ai_json(prompt: str) -> dict:
    raw = ask_ai(prompt, json_mode=True)
    cleaned = raw.strip().strip("```json").strip("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI response was not valid JSON: {raw}") from e