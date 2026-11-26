import random
from core.llm import ask
from core.intake import read_prompt


def get_prompt(name):
    """The prompt file has several sections that start with '### NAME'."""
    text = read_prompt("generate_evals.txt")
    for part in text.split("### ")[1:]:
        head, _, body = part.partition("\n")
        if head.strip() == name:
            return body.strip()
    raise ValueError("prompt section not found: " + name)


def fill(prompt, **kw):
    for k, v in kw.items():
        prompt = prompt.replace("{" + k + "}", str(v))
    return prompt


def valid(out):
    return (isinstance(out.get("question"), str) and len(out["question"]) > 8
            and isinstance(out.get("key_facts"), list) and len(out["key_facts"]) > 0)


def generate_evals(agent, index, n_answer=10, n_edge=4, n_oos=8, seed=1):
    random.seed(seed)
    req = agent["requirements"]
    chunks = [c for c in index.chunks if len(c["text"]) > 150] or index.chunks
    cases = []

    # 1. answerable questions
    picks = random.sample(chunks, min(n_answer, len(chunks)))
    while len(picks) < n_answer:                 # small docs: reuse chunks
        picks.append(random.choice(chunks))
    asked = {}
    for c in picks:
        key = (c["source"], c["page"], c["text"][:30])
        asked.setdefault(key, [])
        for _ in range(2):                       # retry once if JSON is bad
            out = ask(fill(get_prompt("ANSWERABLE"), source=c["source"], text=c["text"],
                           asked=asked[key] or "none"), json_mode=True)
            if valid(out):
                asked[key].append(out["question"])
                cases.append({"type": "answerable", "question": out["question"],
                              "expected_sources": [c["source"]],
                              "key_facts": [str(f) for f in out["key_facts"]]})
                break

    # 2. edge cases: questions that span two documents, and vague questions
    files = sorted({c["source"] for c in chunks})
    n_multi = n_edge // 2 if len(files) >= 2 else 0
    for _ in range(n_multi):
        f1, f2 = random.sample(files, 2)
        a = random.choice([c for c in chunks if c["source"] == f1])
        b = random.choice([c for c in chunks if c["source"] == f2])
        out = ask(fill(get_prompt("MULTI"), source_a=a["source"], text_a=a["text"],
                       source_b=b["source"], text_b=b["text"]), json_mode=True)
        if valid(out):
            cases.append({"type": "edge_multi_doc", "question": out["question"],
                          "expected_sources": [f1, f2],
                          "key_facts": [str(f) for f in out["key_facts"]]})
    for _ in range(n_edge - n_multi):
        c = random.choice(chunks)
        out = ask(fill(get_prompt("AMBIGUOUS"), source=c["source"], text=c["text"]), json_mode=True)
        if valid(out):
            cases.append({"type": "edge_ambiguous", "question": out["question"],
                          "expected_sources": [c["source"]],
                          "key_facts": [str(f) for f in out["key_facts"]]})

    # 3. out-of-scope questions that must be refused
    docs = "\n".join(f"- {f}" for f in files)
    refuse = ", ".join(req.get("must_refuse_topics", [])) or "none"
    out = ask(fill(get_prompt("OUT_OF_SCOPE"), docs=docs, scope=req["scope"],
                   refuse=refuse, n=n_oos), json_mode=True)
    oos = [q for q in out.get("questions", []) if isinstance(q, str)]
    for t in req.get("ungrounded_topics", [])[:2]:      # topics the guard flagged
        oos.insert(0, f"Tell me about {t}.")
    for q in oos[:n_oos]:
        cases.append({"type": "out_of_scope", "question": q,
                      "expected_sources": [], "key_facts": []})

    for i, c in enumerate(cases):
        c["id"] = f"C{i + 1:02d}"
    print(f"[evalgen] generated {len(cases)} cases")
    return cases