# Quality report: ShipPartAssistant

**Brief:** I need an assistant for the procurement team that answers questions about ship spare parts: part prices, stock levels, lead times and supplier terms, and can calculate order totals.

**Final score:** 90.9% (20/22 cases) | run time 52.5 min | eval cases: 22

## Requirements and groundability
- Scope: The AI agent will assist the procurement team in answering questions about ship spare parts, including part prices, stock levels, lead times, and supplier terms, and will calculate order totals. NOTE: the agent must NOT answer about: stock levels.
- Audience: The procurement team of a ship company.
- Tone: Professional and informative.
- Must answer: ['part prices', 'lead times', 'supplier terms', 'calculate order totals']
- Must refuse: ['personal information', 'sensitive data', 'non-essential product information', 'non-ship spare parts information', 'stock levels (not covered by the documents)']
- Topic 'part prices': **partial** (retrieval score 0.642). The excerpts contain information about part prices but do not provide a comprehensive overview of all part prices and their suppliers.
- Topic 'stock levels': **no** (retrieval score 0.554). The excerpts do not contain any information related to stock levels.
- Topic 'lead times': **partial** (retrieval score 0.525). The lead times are provided, but not all parts have lead times listed.
- Topic 'supplier terms': **partial** (retrieval score 0.738). The excerpts contain payment and delivery terms but do not provide specific information about the supplier terms for the given parts.
- Topic 'calculate order totals': **partial** (retrieval score 0.505). Not all aspects of calculating order totals are covered in the provided excerpts, such as the calculation of order totals for different scenarios (e.g., discounts, minimum order value, shipping costs, etc.)

**Tools attached:** ['calculator', 'current_date', 'csv_lookup']

## Scorecard per iteration
| Iteration | Score | Passed | By type | Kept? |
|---|---|---|---|---|
| 0 | 77.3% | 17/22 | {'answerable': '6/10', 'edge_multi_doc': '1/2', 'edge_ambiguous': '2/2', 'out_of_scope': '8/8'} | yes |
| 1 | 90.9% | 20/22 | {'answerable': '8/10', 'edge_multi_doc': '2/2', 'edge_ambiguous': '2/2', 'out_of_scope': '8/8'} | yes |
| 2 | 77.3% | 17/22 | {'answerable': '6/10', 'edge_multi_doc': '1/2', 'edge_ambiguous': '2/2', 'out_of_scope': '8/8'} | reverted |

## Iteration log
### Iteration 1
Score 77.3% -> 90.9% (kept). Failure categories: {'wrong refusal': 1, 'prompt defect': 1, 'hallucination': 3}
- **hallucination**: appended rule to system prompt: Use ONLY facts that appear in the CONTEXT. Never add numbers, names or details that are not in the CONTEXT. If unsure, leave it out.
  - why: answers contained unsupported claims
  - addressed cases: ['C02', 'C05', 'C10']
- **wrong refusal**: appended rule to system prompt: If the CONTEXT contains information that answers the question, even partly, give that answer with its source. Refuse only when the CONTEXT has nothing relevant.
  - why: agent refused although the context had the answer
  - addressed cases: ['C01']
- **prompt defect**: appended rule to system prompt: Do not provide information about shipping costs for returns or any discounts not directly related to part prices, lead times, or supplier terms. Adhere strictly to the provided topics: part prices, lead times, supplier terms, and calculate order totals.
  - why: agent answered out-of-scope questions or missed expected facts
  - addressed cases: ['C11']
### Iteration 2
Score 90.9% -> 77.3% (reverted, it did not improve). Failure categories: {'prompt defect': 2}
- **prompt defect**: appended rule to system prompt: Do not provide information about shipping costs or discounts not directly related to part prices, lead times, or supplier terms. Adhere strictly to the provided topics: part prices, lead times, supplier terms, and calculate order totals. Use ONLY facts that appear in the CONTEXT. Never provide information about shipping costs for returns or any discounts not directly related to part prices, lead times, or supplier terms.
  - why: agent answered out-of-scope questions or missed expected facts
  - addressed cases: ['C03', 'C10']

## What still fails and why
- **C03** (answerable, category: prompt defect): What is the governing law for this agreement?
  - agent said: 'The governing law for this agreement is the laws of the State of California.'
  - expected facts: ['governed by and construed in accordance with the laws of the State of California'] | expected sources: ['supplier_beta.txt'] | retrieved: ['supplier_alpha.txt', 'supplier_beta.txt']
- **C10** (answerable, category: prompt defect): What is the additional cost for expedited shipping?
  - agent said: 'The additional cost for expedited shipping is 10 USD.'
  - expected facts: ['additional cost of 10 USD'] | expected sources: ['supplier_alpha.txt'] | retrieved: ['supplier_alpha.txt']

## Judge reliability
- Pass/fail uses deterministic checks: key-fact match, source match, refusal-phrase match, numbers and word overlap against the retrieved context.
- A second, different model (llama3.2:3b) gives a grounding opinion that is only logged. This reduces self-preference. Verbosity bias is reduced because length is never scored.
- LLM judge and deterministic check disagreed on 14 of 14 answered cases in the final run.

## Known limits
- Agent and judge are small 3B models, so wording errors and misses are expected.
- The eval set is generated from the same documents the agent uses, so it can be easier than real user questions.
- Key-fact matching is string based, so a correct answer in different words can be marked wrong.
- Word-overlap grounding can miss subtle wrong claims that reuse words from the context.