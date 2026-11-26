from core.llm import ask
from core.ingest import load_docs, Index

print(ask("Say hello in one line"))
print(ask('Return JSON with key "color" and value "blue"', json_mode=True))

chunks = load_docs("docs")
idx = Index(chunks)
for r in idx.retrieve("how many sick days do I get?", k=2):
    print(round(r["score"], 2), r["source"], "->", r["text"][:80])