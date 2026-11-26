def write_report(path, brief, req, ground, agent, scorecard, log, results, n_cases, seconds):
    final = scorecard[-1] if scorecard[-1]["accepted"] else [s for s in scorecard if s["accepted"]][-1]
    L = []
    L.append(f"# Quality report: {agent['name']}\n")
    L.append(f"**Brief:** {brief}\n")
    L.append(f"**Final score:** {final['score']*100:.1f}% ({final['passed']}/{final['total']} cases) "
             f"| run time {seconds/60:.1f} min | eval cases: {n_cases}\n")
    if final["score"] >= 1.0:
        L.append("> Warning: 100% on a self-generated eval set is suspicious. The eval set may be too easy.\n")

    L.append("## Requirements and groundability")
    L.append(f"- Scope: {req['scope']}\n- Audience: {req['audience']}\n- Tone: {req['tone']}")
    L.append(f"- Must answer: {req['must_answer_topics']}\n- Must refuse: {req['must_refuse_topics']}")
    for g in ground:
        L.append(f"- Topic '{g['topic']}': **{g['status']}** (retrieval score {g['top_score']}). {g['reason']}")
    L.append(f"\n**Tools attached:** {agent['tools'] or 'none'}\n")

    L.append("## Scorecard per iteration")
    L.append("| Iteration | Score | Passed | By type | Kept? |\n|---|---|---|---|---|")
    for s in scorecard:
        L.append(f"| {s['iteration']} | {s['score']*100:.1f}% | {s['passed']}/{s['total']} | {s['by_type']} | {'yes' if s['accepted'] else 'reverted'} |")

    L.append("\n## Iteration log")
    if not log:
        L.append("No iterations were needed or possible.")
    for e in log:
        L.append(f"### Iteration {e['iteration']}")
        if "score_before" in e:
            L.append(f"Score {e['score_before']*100:.1f}% -> {e['score_after']*100:.1f}% "
                     f"({'kept' if e['accepted'] else 'reverted, it did not improve'}). "
                     f"Failure categories: {e['failure_categories']}")
        for c in e["changes"]:
            L.append(f"- **{c['category']}**: {c['what']}\n  - why: {c['why']}\n  - addressed cases: {c['addresses']}")
        if e.get("note"):
            L.append(e["note"])

    L.append("\n## What still fails and why")
    bad = [r for r in results if not r["passed"]]
    if not bad:
        L.append("Nothing failed in the final run.")
    for r in bad:
        L.append(f"- **{r['id']}** ({r['type']}, category: {r.get('category')}): {r['question']}")
        L.append(f"  - agent said: {r['answer'][:200]!r}")
        L.append(f"  - expected facts: {r['key_facts']} | expected sources: {r['expected_sources']} | retrieved: {r['retrieved_sources']}")

    judged = [r for r in results if r.get("llm_grounded") is not None]
    dis = sum(1 for r in judged if r["llm_grounded"] != r["grounded"])
    L.append("\n## Judge reliability")
    L.append("- Pass/fail uses deterministic checks: key-fact match, source match, refusal-phrase match, "
             "numbers and word overlap against the retrieved context.")
    L.append("- A second, different model (llama3.2:3b) gives a grounding opinion that is only logged. "
             "This reduces self-preference. Verbosity bias is reduced because length is never scored.")
    L.append(f"- LLM judge and deterministic check disagreed on {dis} of {len(judged)} answered cases in the final run.")

    L.append("\n## Known limits")
    L.append("- Agent and judge are small 3B models, so wording errors and misses are expected.")
    L.append("- The eval set is generated from the same documents the agent uses, so it can be easier than real user questions.")
    L.append("- Key-fact matching is string based, so a correct answer in different words can be marked wrong.")
    L.append("- Word-overlap grounding can miss subtle wrong claims that reuse words from the context.")
    open(path, "w", encoding="utf-8").write("\n".join(L))