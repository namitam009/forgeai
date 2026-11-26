# ForgeAI: an agent that builds, tests and improves agents

**Built by:** Namita Mishra  |  

ForgeAI takes a one-paragraph brief and a folder of documents (PDF / CSV / TXT) and produces
a tested agent definition and an honest quality report. Everything runs locally on small
open models through Ollama. AI tools helped me write the code (the assignment allows this);
I ran, debugged and tuned every stage myself, and the problems below are real ones I hit.

## How to run

    ollama pull qwen2.5:3b          # the agent / generator model
    ollama pull llama3.2:3b         # a different model, used as second-opinion judge
    ollama pull nomic-embed-text    # embeddings
    pip install -r requirements.txt

    # run the factory (unattended)
    python forge.py --brief brief.txt --docs ./docs --out runs/new --auto

    # without --auto: it interviews you (max 5 questions) and asks you to approve the requirements
    python forge.py --brief brief.txt --docs ./docs --out runs/new

    # chat with any generated agent
    python runner.py runs/new/agent.json

A full run takes roughly 20 to 50 minutes on a laptop CPU, because every eval case needs several model calls.

## Pipeline

intake (max 5 questions) -> requirements -> groundability guard -> agent generator
-> eval generator -> judge -> critic-optimizer (max 3 iterations) -> report

| Requirement | Where |
|---|---|
| 1. Intake interviewer (max 5 questions, enforced in code) | core/intake.py |
| 2. Groundability guard | core/groundability.py |
| 3. Agent generator + tool selection | core/generator.py, tools/registry.py |
| 4. Eval generator (20+ cases, generated, prompts committed) | core/evalgen.py, prompts/generate_evals.txt |
| 5. Judge | core/judge.py, prompts/judge.txt |
| 6. Critic-optimizer loop (max 3) | core/optimizer.py |
| 7. Honest report | core/report.py |
| 8. Generic chat runner | runner.py, core/agent_runtime.py |
| 9. Two full demos | runs/hr_policy, runs/ship_spares |

## Design decisions

- **Groundability guard.** For every must-answer topic I retrieve chunks and use two checks.
  If the best retrieval score is below 0.5, the topic is marked unsupported without asking the LLM.
  Otherwise the LLM says yes / partial / no. If the LLM says "no" but retrieval is strong (>= 0.55),
  I downgrade it to "partial", because a lone 3B-model "no" is not trustworthy.
  Unsupported topics move to must-refuse and the scope text is updated, so the agent is never told to answer them.
- **Tool selection.** The LLM proposes tools, then code filters them. A tool is kept only if the
  brief contains matching words (weather needs "weather", "forecast" and so on). The CSV tool is kept only if a CSV is in the folder.
- **Evals are generated from the documents**: answerable, two-document, ambiguous and
  out-of-scope questions, minimum 20 (forge.py tops up with new seeds if some generations fail).
- **Judge.** Pass / fail is deterministic: expected key facts, expected source, refusal phrase,
  and numbers and word overlap checked against the retrieved context. A different model (llama3.2)
  gives a second grounding opinion that is logged but does not decide. A different model reduces self-preference,
  and length is never scored, which reduces verbosity bias. Position bias does not apply because
  I score one answer at a time and do not compare two.
- **Optimizer.** Each failure goes into one of four categories: retrieval miss, hallucination,
  wrong refusal, prompt defect. Each category changes only its own part (retrieval settings, or one rule
  appended to the prompt). The fix is kept only if the score goes up, otherwise it is reverted and the loop stops.

## Demo runs (all artifacts committed in runs/)

| Demo | Brief | Score (iteration 0 -> final) | Tools |
|---|---|---|---|
| HR policy (`runs/hr_policy`) | HR questions for shore staff, plus an ungroundable ask for individual salary and bonus | <HR_SCORE> | none needed for the HR brief |
| Ship spares (`runs/ship_spares`) | Procurement assistant: prices, stock, lead times, supplier terms, order totals | 77.3% -> 90.9% (22 cases, 52.5 min) | csv_lookup, calculator, current_date |

Each run folder has: brief, interview, requirements, groundability, initial and final agent definition,
evals, results per iteration, iteration log, scorecard and report. `runs/test_full` is an extra small run on a toy folder.
Document synthesis prompts are in `make_docs.py`.

## Problems I faced and how I fixed them

1. **First eval score was 31.8% and every answerable case failed.** The answers were correct. The 3B LLM judge
   marked them "not grounded". In the ship run the LLM judge disagreed with the deterministic check on
   14 of 14 answered cases. I made the deterministic check the decision maker and kept the LLM judge as a logged second opinion. Score went to 77.3%.
2. **CEO-salary topic scored 0.442 against a 0.45 threshold**, too close to the line. I raised it to 0.5.
3. **One topic appeared in both must-answer and must-refuse** after a confusing interview answer. I added a clash check in code.
4. **A KeyError in the judge** from a half-edited file. Every result key is now created in one place.
5. **Stock levels were wrongly flagged as unsupported in the ship run**, although stock is in the CSV.
   A single LLM "no" overruled decent retrieval (score 0.554), so the committed ship agent refuses stock questions.
   I fixed the guard in code afterwards (strong retrieval downgrades a lone "no" to "partial"),
   **but I did not re-run the ship demo because a run takes about 50 minutes. The committed ship artifacts were made with the old guard.**
6. **Small models return broken JSON.** `llm.py` retries 3 times and every stage fills in missing keys.
7. **Fewer than 20 eval cases** when some generations failed. forge.py now tops up with new seeds.
8. **Optimizer iteration 2 lowered the score in both runs** (for example 90.9% -> 77.3% in ship spares).
   The loop reverted it and stopped, which is the behaviour I wanted.

## What still fails (see each run's report.md)

- Two ship-spares answers marked wrong (C03, C10) look correct on reading: the agent gave
  the right facts in different words and my strict key-fact string match missed them.
  The true score is probably a bit higher than 90.9%. The report classifies them as "prompt defect", which is a misclassification caused by the matcher.
- The ship agent refuses stock-level questions because of problem 5 above.

## Known limits

- 3B models: wording mistakes and misses are expected.
- The eval set is generated from the same documents the agent uses, so it can be easier than real user questions.
- Key-fact matching is string based, so correct paraphrases can fail.
- Word-overlap grounding can miss subtle wrong claims that reuse words from the context.
- The failure classifier uses simple rules, so some failures land in "prompt defect" by default.
- Scanned PDFs without text are not supported (no OCR).
- Not done: stretch goals other than the human approval checkpoint (run without `--auto`).
- The factory has been tested on two document sets plus a toy set; an unusual brief or file type may still break something.