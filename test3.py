import json, os
from core.ingest import load_docs, Index
from core.intake import interview, write_requirements
from core.groundability import check_groundability
from core.generator import generate_agent

brief = "I need an assistant that answers leave policy questions for employees."
chunks = load_docs("docs")
index = Index(chunks)
answers = interview(brief, chunks, auto=True)   # auto=True so it does not ask you
req = write_requirements(brief, chunks, answers)
req, _ = check_groundability(req, index)
agent = generate_agent(brief, req, "docs")

os.makedirs("runs/test", exist_ok=True)
json.dump(agent, open("runs/test/agent.json", "w", encoding="utf-8"), indent=2)
print("tools attached:", agent["tools"])