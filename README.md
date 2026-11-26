# ForgeAI: an agent that builds, tests and improves agents

ForgeAI takes a one-paragraph brief and a folder of documents (PDF/CSV/TXT) and produces
a tested agent definition plus an honest quality report. It runs on local models via Ollama.

## Run it
    ollama pull qwen2.5:3b
    ollama pull llama3.2:3b
    ollama pull nomic-embed-text
    pip install -r requirements.txt
    python forge.py --brief brief.txt --docs ./docs --out runs/new --auto
    python runner.py runs/new/agent.json        # chat with the generated agent

Without `--auto` it interviews you (max 5 questions) and asks you to approve the requirements.

## Pipeline
intake (max 5 questions) -> requirements -> groundability guard -> agent generator
-> eval generator -> judge -> critic-optimizer (max 3 iterations) -> report

## Design decisions
- **Groundability guard:** a topic is dropped if the best retrieval score is below 0.5 or
  the LLM says the excerpts do not support it. Dropped topics move to must-refuse.
- **Tool selection:** the LLM proposes tools, then code filters them. A tool is kept only
  if the brief contains matching words (weather tool needs "weather" etc.). CSV lookup needs a CSV in the folder.
- **Evals are generated from the documents**, not hand-written (prompts/generate_evals.txt):
  answerable, multi-document, ambiguous, and out-of-scope cases. Minimum 20.
- **Judge:** pass/fail is deterministic (key facts, source match, refusal phrase, numbers and
  word overlap vs the retrieved context). A different model (llama3.2) gives a second
  grounding opinion that is only logged. Different model = less self-preference; length is
  never scored = less verbosity bias.
- **Optimizer:** failures are classified (retrieval miss / hallucination / wrong refusal /
  prompt defect). Each category changes only its own part. A fix is kept only if the score improves.

## Problems I faced and how I fixed them
1. **First eval score was 31.8% and every answerable case failed.** The answers were
   correct. The 3B LLM judge marked them "not grounded". I made grounding deterministic
   and kept the LLM judge only as a logged second opinion. Score went to 77.3%.
2. **CEO-salary topic scored 0.442 against a 0.45 threshold**, too close to the line. I raised it to 0.5.
3. **A topic appeared in both must-answer and must-refuse** after a confusing interview answer. I added a clash check in code.
4. **A KeyError in the judge** from a half-edited file. Every result key is now created in one place.
5. **Stock levels flagged as unsupported although they are in the CSV.** A lone LLM "no"
   overruled decent retrieval. I made the guard trust retrieval score when it is high.
6. **Small model returns broken JSON.** `llm.py` retries 3 times and every stage fills in missing keys.
7. **Fewer than 20 eval cases** when some generations failed. forge.py now tops up with new seeds.

## Demo runs (full artifacts in runs/)
| Demo | Final score | Notes |
|---|---|---|
| HR policy (runs/hr_policy) | <x>% | salary/bonus flagged as ungroundable |
| Ship spares (runs/ship_spares) | <y>% | csv_lookup + calculator attached |

## Known limits
- 3B models; the eval set is generated from the same documents so it may be easier than real use.
- String-based fact matching can mark a correct paraphrase wrong.
- Word-overlap grounding can miss subtle wrong claims that reuse context words.
- Iterations sometimes lower the score; the optimizer reverts them.
- Scanned PDFs without text are not supported (no OCR).
- Not done: stretch goals other than the human approval checkpoint.
