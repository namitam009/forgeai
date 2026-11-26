import json
from core.agent_runtime import build_index
from core.evalgen import generate_evals
from core.judge import run_all

agent = json.load(open("runs/test/agent.json", encoding="utf-8"))
index = build_index(agent)
cases = generate_evals(agent, index)
json.dump(cases, open("runs/test/evals.json", "w", encoding="utf-8"), indent=2)

results, score = run_all(agent, index, cases)
json.dump(results, open("runs/test/results.json", "w", encoding="utf-8"), indent=2)
print("SCORE:", score)