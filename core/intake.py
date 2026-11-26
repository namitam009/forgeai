import os
from core.llm import ask


def read_prompt(name):
    with open(os.path.join("prompts", name), encoding="utf-8") as f:
        return f.read()


def doc_summary(chunks):
    """One line per document: filename + first 200 characters."""
    seen = {}
    for c in chunks:
        if c["source"] not in seen:
            seen[c["source"]] = c["text"][:200].replace("\n", " ")
    return "\n".join(f"- {name}: {text}" for name, text in seen.items())


def get_questions(brief, chunks):
    prompt = read_prompt("intake_questions.txt")
    prompt = prompt.replace("{brief}", brief).replace("{docs}", doc_summary(chunks))
    result = ask(prompt, json_mode=True)
    questions = [q for q in result.get("questions", []) if isinstance(q, str)]
    return questions[:5]  # hard limit of 5, enforced in code


def interview(brief, chunks, auto=False):
    """Ask the requester the questions in the terminal. auto=True skips input()."""
    answers = []
    for q in get_questions(brief, chunks):
        if auto:
            a = "No preference, use your best judgement."
        else:
            a = input(f"\n? {q}\n> ")
        answers.append({"question": q, "answer": a})
    return answers


def write_requirements(brief, chunks, answers):
    qa = "\n".join(f"Q: {a['question']}\nA: {a['answer']}" for a in answers) or "No questions asked."
    prompt = read_prompt("write_requirements.txt")
    prompt = (prompt.replace("{brief}", brief)
                    .replace("{docs}", doc_summary(chunks))
                    .replace("{answers}", qa))
    req = ask(prompt, json_mode=True)
    # make sure every key exists, even if the small model forgot one
    clean = {
        "scope": str(req.get("scope", brief)),
        "audience": str(req.get("audience", "general users")),
        "tone": str(req.get("tone", "professional and clear")),
        "must_answer_topics": [str(t) for t in req.get("must_answer_topics", [])],
        "must_refuse_topics": [str(t) for t in req.get("must_refuse_topics", [])],
    }
    return clean