import json

res = json.load(open("runs/test/results.json", encoding="utf-8"))
for r in res[:4]:
    print("=" * 60)
    print("ID:", r["id"], r["type"])
    print("QUESTION:", r["question"])
    print("ANSWER:", r["answer"][:300])
    print("refused:", r["refused"], "| facts_ratio:", r["facts_ratio"],
          "| grounded:", r["grounded"], "| retrieval_ok:", r["retrieval_ok"])
    print("key_facts:", r["key_facts"])
    print("retrieved:", r["retrieved_sources"])