import json
from core.llm import ask
from core.ingest import load_docs, Index
from tools.registry import TOOLS


def build_index(agent):
    r = agent["retrieval"]
    chunks = load_docs(agent["docs_folder"], r["chunk_size"], r["overlap"])
    return Index(chunks)


def run_agent(agent, index, question):
    r = agent["retrieval"]
    hits = [h for h in index.retrieve(question, k=r["top_k"]) if h["score"] >= r["min_score"]]
    refusal = agent["output_contract"]["refusal_message"]

    if not hits and not agent["tools"]:
        return {"answer": refusal, "sources": [], "hits": [], "tool_used": None}

    context = "\n\n".join(f"[{h['source']} p{h['page']}] {h['text']}" for h in hits) or "(none)"
    tool_text = ""
    if agent["tools"]:
        lines = [f"- {t}: {TOOLS[t]['description']}" for t in agent["tools"]]
        tool_text = ("\n\nYou may use a tool. To use one, reply with ONLY this JSON and nothing else: "
                     '{"tool": "<name>", "input": "<text>"}\nTools:\n' + "\n".join(lines))

    prompt = (f"{agent['system_prompt']}{tool_text}\n\nCONTEXT:\n{context}\n\n"
              f"QUESTION: {question}\n\nANSWER:")
    answer = ask(prompt)
    tool_used = None

    # did the model ask for a tool?
    if answer.startswith("{") and '"tool"' in answer:
        try:
            call = json.loads(answer)
            name = call["tool"]
            if name in agent["tools"]:
                result = TOOLS[name]["fn"](call.get("input", ""), docs_folder=agent["docs_folder"])
                tool_used = {"tool": name, "input": call.get("input", ""), "result": result}
                prompt2 = (f"{agent['system_prompt']}\n\nCONTEXT:\n{context}\n\n"
                           f"TOOL RESULT ({name}): {result}\n\nQUESTION: {question}\n\n"
                           "Answer the question using the context and the tool result.\nANSWER:")
                answer = ask(prompt2)
        except Exception as e:
            answer = f"(tool error: {e})"

    sources = sorted({h["source"] for h in hits})
    return {"answer": answer, "sources": sources, "hits": hits, "tool_used": tool_used}