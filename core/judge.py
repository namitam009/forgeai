import re
from core.llm import ask
from core.intake import read_prompt
from core.agent_runtime import run_agent

# A different model from the agent's model, to reduce self-preference bias.
JUDGE_MODEL = "llama3.2:3b"

REFUSAL_MARKERS = ["can't answer", "cannot answer", "can not answer", "outside what i can support"]


def is_refusal(answer):
    a = answer.lower().replace("\u2019", "'")
    return any(m in a for m in REFUSAL_MARKERS)


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9. ]", " ", str(s).lower())).strip()


def facts_found(answer, key_facts):
    """Deterministic check: how many expected key facts appear in the answer."""
    if not key_facts:
        return 1.0
    a = norm(answer)
    return sum(1 for f in key_facts if norm(f) in a) / len(key_facts)


def numbers_supported(answer, context):
    """Every number in the answer must also appear in the context."""
    nums = re.findall(r"\d+(?:\.\d+)?", answer)
    ctx = set(re.findall(r"\d+(?:\.\d+)?", context))
    return all(n in ctx for n in nums)


def word_overlap(answer, context):
    """Share of the answer's meaningful words that also appear in the context."""
    words = [w for w in norm(answer).split() if len(w) > 3]
    if not words:
        return 1.0
    ctx = set(norm(context).split())
    return sum(1 for w in words if w in ctx) / len(words)


def llm_grounded(answer, context):
    """LLM judge, used only as a logged second opinion."""
    prompt = read_prompt("judge.txt").replace("{context}", context).replace("{answer}", answer)
    try:
        out = ask(prompt, json_mode=True, model=JUDGE_MODEL)
        return str(out.get("grounded", "yes")).lower() == "yes"
    except Exception as e:
        print("[judge] LLM judge failed, treating as grounded:", e)
        return True


def evaluate_case(agent, index, case):
    res = run_agent(agent, index, case["question"])
    answer = res["answer"]
    refused = is_refusal(answer)
    retrieved = sorted({h["source"] for h in res["hits"]})
    r = {"id": case["id"], "type": case["type"], "question": case["question"],
         "answer": answer, "refused": refused, "retrieved_sources": retrieved,
         "expected_sources": case["expected_sources"], "key_facts": case["key_facts"],
         "facts_ratio": None, "retrieval_ok": None, "grounded": None, "llm_grounded": None}

    if case["type"] == "out_of_scope":
        r["passed"] = refused                      # fully deterministic
    else:
        r["facts_ratio"] = facts_found(answer, case["key_facts"])
        r["retrieval_ok"] = all(s in retrieved for s in case["expected_sources"])
        context = "\n".join(h["text"] for h in res["hits"])
        if res["tool_used"]:
            context += "\n" + str(res["tool_used"]["result"])
        if refused:
            r["grounded"] = True
        else:
            r["grounded"] = bool(numbers_supported(answer, context)
                                 and word_overlap(answer, context) >= 0.6)
            r["llm_grounded"] = llm_grounded(answer, context)   # logged only
        r["passed"] = bool((not refused) and r["facts_ratio"] >= 0.6 and r["grounded"])
    return r


def run_all(agent, index, cases):
    results = []
    for case in cases:
        r = evaluate_case(agent, index, case)
        print(f"[eval] {r['id']} {r['type']:<15} {'PASS' if r['passed'] else 'FAIL'}")
        results.append(r)
    score = sum(r["passed"] for r in results) / len(results)
    return results, round(score, 3)