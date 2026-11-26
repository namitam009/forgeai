import copy, json, os
from core.llm import ask
from core.intake import read_prompt
from core.judge import run_all

# Fixed rules for the two clear-cut failure types.
RULES = {
    "hallucination": "Use ONLY facts that appear in the CONTEXT. Never add numbers, names or details that are not in the CONTEXT. If unsure, leave it out.",
    "wrong refusal": "If the CONTEXT contains information that answers the question, even partly, give that answer with its source. Refuse only when the CONTEXT has nothing relevant.",
}


def classify(r):
    """Put every failure into exactly one of the 4 categories."""
    if r["type"] == "out_of_scope":
        return "prompt defect"            # it answered something it should refuse
    if not r["retrieval_ok"]:
        return "retrieval miss"           # expected source was not retrieved
    if r["refused"]:
        return "wrong refusal"            # source was there, but it still refused
    if not r["grounded"]:
        return "hallucination"            # answer has claims not in the context
    return "prompt defect"                # retrieved, not refused, but key facts missing


def propose_rule(agent, failures):
    lines = []
    for r in failures[:5]:
        lines.append(f"- [{r['type']}] Q: {r['question']} | A: {r['answer'][:150]} | expected facts: {r['key_facts']}")
    prompt = (read_prompt("classify_failure.txt")
              .replace("{system_prompt}", agent["system_prompt"])
              .replace("{cases}", "\n".join(lines)))
    try:
        rule = str(ask(prompt, json_mode=True).get("rule", "")).strip()
    except Exception:
        rule = ""
    return rule


def apply_fixes(agent, failures):
    """Targeted fixes: each category changes only its own part of the agent."""
    groups = {}
    for r in failures:
        groups.setdefault(r["category"], []).append(r)
    changes = []
    ret = agent["retrieval"]

    if "retrieval miss" in groups:
        old = (ret["top_k"], ret["min_score"])
        ret["top_k"] = min(ret["top_k"] + 2, 8)
        ret["min_score"] = round(max(ret["min_score"] - 0.1, 0.2), 2)
        if (ret["top_k"], ret["min_score"]) != old:
            changes.append({"category": "retrieval miss",
                            "what": f"top_k {old[0]}->{ret['top_k']}, min_score {old[1]}->{ret['min_score']}",
                            "why": "expected source document was not among the retrieved chunks",
                            "addresses": [r["id"] for r in groups["retrieval miss"]]})

    for cat in ("hallucination", "wrong refusal"):
        if cat in groups and RULES[cat] not in agent["system_prompt"]:
            agent["system_prompt"] += "\n- " + RULES[cat]
            changes.append({"category": cat, "what": "appended rule to system prompt: " + RULES[cat],
                            "why": "answers contained unsupported claims" if cat == "hallucination"
                                   else "agent refused although the context had the answer",
                            "addresses": [r["id"] for r in groups[cat]]})

    if "prompt defect" in groups:
        rule = propose_rule(agent, groups["prompt defect"])
        if rule and rule not in agent["system_prompt"]:
            agent["system_prompt"] += "\n- " + rule
            changes.append({"category": "prompt defect", "what": "appended rule to system prompt: " + rule,
                            "why": "agent answered out-of-scope questions or missed expected facts",
                            "addresses": [r["id"] for r in groups["prompt defect"]]})
    return agent, changes


def scorecard_row(it, score, results, accepted=True):
    types = {}
    for r in results:
        t = types.setdefault(r["type"], [0, 0])
        t[0] += r["passed"]
        t[1] += 1
    return {"iteration": it, "score": score, "passed": sum(r["passed"] for r in results),
            "total": len(results), "accepted": accepted,
            "by_type": {k: f"{v[0]}/{v[1]}" for k, v in types.items()}}


def save(path, obj):
    json.dump(obj, open(path, "w", encoding="utf-8"), indent=2)


def optimize(agent, index, cases, out_dir, max_iter=3):
    results, score = run_all(agent, index, cases)
    save(os.path.join(out_dir, "results_iter0.json"), results)
    scorecard = [scorecard_row(0, score, results)]
    log = []

    for it in range(1, max_iter + 1):
        failures = [r for r in results if not r["passed"]]
        if not failures:
            print("[optimizer] no failures left, stopping")
            break
        for r in failures:
            r["category"] = classify(r)
        print(f"[optimizer] iteration {it}: {len(failures)} failures")

        new_agent, changes = apply_fixes(copy.deepcopy(agent), failures)
        if not changes:
            log.append({"iteration": it, "changes": [], "note": "no further fix possible, stopped"})
            break

        new_results, new_score = run_all(new_agent, index, cases)
        save(os.path.join(out_dir, f"results_iter{it}.json"), new_results)
        accepted = new_score > score
        log.append({"iteration": it, "score_before": score, "score_after": new_score,
                    "accepted": accepted, "changes": changes,
                    "failure_categories": {c: sum(1 for r in failures if r["category"] == c)
                                           for c in {r["category"] for r in failures}}})
        scorecard.append(scorecard_row(it, new_score, new_results, accepted))
        if accepted:                      # keep the fix only if the score really improved
            agent, results, score = new_agent, new_results, new_score
        else:
            print("[optimizer] fix did not help, reverted and stopped")
            break

    for r in results:
        if not r["passed"]:
            r["category"] = classify(r)
    return agent, results, scorecard, log