import json
from core.ingest import load_docs, Index
from core.intake import interview, write_requirements
from core.groundability import check_groundability

brief = ("I need an assistant that answers leave policy questions for employees "
         "and also tells them the CEO's salary.")

chunks = load_docs("docs")
index = Index(chunks)
answers = interview(brief, chunks)          # answer the questions in the terminal
req = write_requirements(brief, chunks, answers)
req, results = check_groundability(req, index)
print(json.dumps(req, indent=2))