import argparse, json, os, sys, time
from core.ingest import load_docs, Index
from core.intake import interview, write_requirements
from core.groundability import check_groundability
from core.generator import generate_agent
from core.evalgen import generate_evals
from core.optimizer import optimize
from core.report import write_report


def save(out, name, obj):
    json.dump(obj, open(os.path.join(out, name), "w", encoding="utf-8"), indent=2)


def main():
    ap = argparse.ArgumentParser(description="ForgeAI: builds, tests and improves an agent")
    ap.add_argument("--brief", required=True, help="text file with the one-paragraph brief")
    ap.add_argument("--docs", required=True, help="folder with pdf / csv / txt documents")
    ap.add_argument("--out", required=True, help="output folder for all artifacts")
    ap.add_argument("--auto", action="store_true", help="unattended: skip questions and approval")
    args = ap.parse_args()

    t0 = time.time()
    os.makedirs(args.out, exist_ok=True)
    brief = open(args.brief, encoding="utf-8").read().strip()
    open(os.path.join(args.out, "brief.txt"), "w", encoding="utf-8").write(brief)

    print("[1/7] reading and indexing documents")
    if not os.path.isdir(args.docs):
        sys.exit("docs folder not found: " + args.docs)
    chunks = load_docs(args.docs)
    if not chunks:
        sys.exit("no readable text found in the docs folder (empty folder or scanned PDFs?)")
    index = Index(chunks)

    print("[2/7] intake interview")
    answers = interview(brief, chunks, auto=args.auto)
    save(args.out, "interview.json", answers)
    req = write_requirements(brief, chunks, answers)

    print("[3/7] groundability guard")
    req, ground = check_groundability(req, index)
    save(args.out, "groundability.json", ground)

    if not args.auto:                                   # human checkpoint
        print("\nREQUIREMENTS:\n" + json.dumps(req, indent=2))
        a = input("\nApprove? (press y, or type a correction): ").strip()
        if a and a.lower() != "y":
            req["scope"] += " Requester correction: " + a
    save(args.out, "requirements.json", req)

    print("[4/7] generating agent")
    agent = generate_agent(brief, req, args.docs)
    save(args.out, "agent_initial.json", agent)

    print("[5/7] generating eval set")
    cases = generate_evals(agent, index)
    seed = 2
    while len(cases) < 20 and seed < 6:          # top up if some generations failed
        more = generate_evals(agent, index, seed=seed)
        seen = {c["question"] for c in cases}
        cases += [c for c in more if c["question"] not in seen]
        seed += 1
    for i, c in enumerate(cases):
        c["id"] = f"C{i + 1:02d}"
    save(args.out, "evals.json", cases)

    print("[6/7] running evals and optimizing (max 3 iterations)")
    agent, results, scorecard, log = optimize(agent, index, cases, args.out, max_iter=3)
    save(args.out, "agent.json", agent)
    save(args.out, "iteration_log.json", log)
    save(args.out, "scorecard.json", scorecard)

    print("[7/7] writing report")
    write_report(os.path.join(args.out, "report.md"), brief, req, ground, agent,
                 scorecard, log, results, len(cases), time.time() - t0)
    print(f"\nDONE in {(time.time() - t0) / 60:.1f} min. See {args.out}/report.md")


if __name__ == "__main__":
    main()