import requests, json, time

OLLAMA_URL = "http://localhost:11434/api/generate"
EMBED_URL = "http://localhost:11434/api/embeddings"
MODEL = "qwen2.5:3b"
EMBED_MODEL = "nomic-embed-text"


def ask(prompt, json_mode=False, model=MODEL, retries=3):
    """Call the local model. Retries because small models often return broken JSON."""
    for attempt in range(retries):
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2},
            }
            if json_mode:
                payload["format"] = "json"
            r = requests.post(OLLAMA_URL, json=payload, timeout=300)
            text = r.json()["response"].strip()
            return json.loads(text) if json_mode else text
        except Exception as e:
            print(f"[llm] attempt {attempt + 1} failed: {e}")
            time.sleep(1)
    raise RuntimeError("LLM failed after retries")


def embed(text):
    """Turn text into a list of numbers (a vector) so we can search by meaning."""
    r = requests.post(EMBED_URL, json={"model": EMBED_MODEL, "prompt": text}, timeout=120)
    return r.json()["embedding"]