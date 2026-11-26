import sys, json
from core.agent_runtime import build_index, run_agent

if len(sys.argv) < 2:
    print("usage: python runner.py path/to/agent.json")
    sys.exit(1)

agent = json.load(open(sys.argv[1], encoding="utf-8"))
print(f"Loading agent: {agent['name']}  (tools: {agent['tools'] or 'none'})")
index = build_index(agent)
print("Ready. Type your question (or 'quit').\n")

while True:
    q = input("You: ").strip()
    if q.lower() in ("quit", "exit", ""):
        break
    res = run_agent(agent, index, q)
    print("\nAgent:", res["answer"])
    if res["sources"]:
        print("Sources:", ", ".join(res["sources"]))
    if res["tool_used"]:
        print("Tool used:", res["tool_used"]["tool"])
    print()