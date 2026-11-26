from core.llm import ask
from core.intake import read_prompt

# If the best matching chunk scores below this, the topic is treated as unsupported
# without trusting the LLM. 0.442 (CEO salary) vs 0.73 (leave policy) in my test,
# so 0.5 sits safely between the two.
SCORE_THRESHOLD = 0.5


def check_topic(topic, index):
    hits = index.retrieve(topic, k=4)
    top_score = hits[0]["score"] if hits else 0.0
    context = "\n---\n".join(h["text"] for h in hits)

    prompt = read_prompt("groundability.txt")
    prompt = prompt.replace("{topic}", topic).replace("{context}", context)
    verdict = ask(prompt, json_mode=True)

    llm_status = str(verdict.get("status", "no")).lower()
    if llm_status not in ("yes", "partial", "no"):
        llm_status = "no"
    reason = str(verdict.get("reason", ""))

    # deterministic check comes first
    if top_score < SCORE_THRESHOLD:
        status = "no"
        reason = f"best retrieval score {top_score:.2f} is below {SCORE_THRESHOLD}. " + reason
    else:
        status = llm_status

    return {"topic": topic, "status": status, "top_score": round(top_score, 3), "reason": reason}


def check_groundability(req, index):
    """Move topics the docs cannot support from must_answer to must_refuse."""
    results, keep, dropped = [], [], []
    for topic in req["must_answer_topics"]:
        r = check_topic(topic, index)
        results.append(r)
        print(f"[groundability] {topic!r} -> {r['status']} (score {r['top_score']})")
        (dropped if r["status"] == "no" else keep).append(topic)

    # a topic we keep answering must not also sit in the refuse list
    cleaned = []
    for t in req["must_refuse_topics"]:
        clash = any(k.lower() in t.lower() or t.lower() in k.lower() for k in keep)
        if not clash:
            cleaned.append(t)

    req["must_answer_topics"] = keep
    req["must_refuse_topics"] = cleaned + [f"{t} (not covered by the documents)" for t in dropped]
    req["ungrounded_topics"] = dropped
    if dropped:
        req["scope"] += " NOTE: the agent must NOT answer about: " + ", ".join(dropped) + "."
    return req, results