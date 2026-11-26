import os
from core.llm import ask
from core.intake import read_prompt
from tools.registry import TOOLS

REFUSAL = "I'm sorry, I can't answer that. It is outside what I can support from my documents."


def filter_tools(tools, text, docs_folder):
    """Hard safety rule in code: only keep a tool if the brief really justifies it."""
    text = text.lower()
    has_csv = any(f.lower().endswith(".csv") for f in os.listdir(docs_folder))
    final = []
    for t in tools:
        if t not in TOOLS:
            continue
        words = TOOLS[t]["needs_words"]
        if t == "csv_lookup" and has_csv:
            final.append(t)
        elif words and any(w in text for w in words) and t != "csv_lookup":
            final.append(t)
        elif not words:
            final.append(t)
        else:
            print(f"[generator] dropped tool '{t}': brief does not justify it")
    return final


def generate_agent(brief, req, docs_folder):
    tool_text = "\n".join(f"- {n}: {t['description']}" for n, t in TOOLS.items())
    req_text = "\n".join(f"{k}: {v}" for k, v in req.items())
    prompt = read_prompt("generate_agent.txt")
    prompt = prompt.replace("{requirements}", req_text).replace("{tools}", tool_text)
    out = ask(prompt, json_mode=True)

    tools = filter_tools(out.get("tools", []), brief + " " + req_text, docs_folder)
    system_prompt = str(out.get("system_prompt", "")) or \
        f"You are an assistant. Scope: {req['scope']}. Tone: {req['tone']}."
    system_prompt += ("\n\nRULES:\n- Answer only from the CONTEXT given.\n"
                      "- Mention the source file name for every fact.\n"
                      f"- If the context does not contain the answer, reply exactly: {REFUSAL}")

    return {
        "name": str(out.get("name", "Generated Agent")),
        "docs_folder": docs_folder,
        "system_prompt": system_prompt,
        "retrieval": {"chunk_size": 500, "overlap": 100, "top_k": 4, "min_score": 0.45},
        "tools": tools,
        "output_contract": {"format": "answer + sources", "must_cite": True,
                            "refusal_message": REFUSAL},
        "requirements": req,
    }