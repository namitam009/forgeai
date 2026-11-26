# Quality report: PolicyAssistant

**Brief:** I need an assistant that answers leave and travel policy questions for employees, and also tells them the CEO's salary.

**Final score:** 75.0% (12/16 cases) | run time 18.1 min | eval cases: 16

## Requirements and groundability
- Scope: The AI agent will answer questions about leave and travel policies for employees and provide brief information about the CEO's salary. NOTE: the agent must NOT answer about: Sick Leave, Maternity Leave, Economy Class Flights, Business Class Flights, Hotel Reimbursement.
- Audience: Employees of the organization
- Tone: Professional and informative
- Must answer: ['Leave Policy', 'Travel Policy']
- Must refuse: ["CEO's Salary", 'Sick Leave (not covered by the documents)', 'Maternity Leave (not covered by the documents)', 'Economy Class Flights (not covered by the documents)', 'Business Class Flights (not covered by the documents)', 'Hotel Reimbursement (not covered by the documents)']
- Topic 'Leave Policy': **partial** (retrieval score 0.73). The excerpts do not contain information about the Leave Policy for employees who are not full-time, such as contractors or temporary workers.
- Topic 'Sick Leave': **no** (retrieval score 0.746). The excerpts do not contain any information related to sick leave or travel policy as described in the topic.
- Topic 'Maternity Leave': **no** (retrieval score 0.747). The excerpts do not contain any information about maternity leave or travel policy related to maternity leave.
- Topic 'Travel Policy': **partial** (retrieval score 0.712). not all aspects of travel policy are covered in the provided excerpts
- Topic 'Economy Class Flights': **no** (retrieval score 0.681). The excerpts do not contain information about Economy Class Flights, Business Class Flights, or any specific details about Economy Class flights such as pricing, availability, or restrictions.
- Topic 'Business Class Flights': **no** (retrieval score 0.638). The excerpts do not contain information about Business Class Flights or any related policies such as reimbursement for travel, hotel stays, or cab expenses.
- Topic 'Hotel Reimbursement': **no** (retrieval score 0.643). The excerpts do not contain information about Hotel Reimbursement or Cab expenses.

**Tools attached:** none

## Scorecard per iteration
| Iteration | Score | Passed | By type | Kept? |
|---|---|---|---|---|
| 0 | 31.2% | 5/16 | {'answerable': '2/10', 'edge_multi_doc': '1/2', 'edge_ambiguous': '1/2', 'out_of_scope': '1/2'} | yes |
| 1 | 75.0% | 12/16 | {'answerable': '8/10', 'edge_multi_doc': '2/2', 'edge_ambiguous': '1/2', 'out_of_scope': '1/2'} | yes |
| 2 | 62.5% | 10/16 | {'answerable': '8/10', 'edge_multi_doc': '1/2', 'edge_ambiguous': '1/2', 'out_of_scope': '0/2'} | reverted |

## Iteration log
### Iteration 1
Score 31.2% -> 75.0% (kept). Failure categories: {'prompt defect': 1, 'hallucination': 10}
- **hallucination**: appended rule to system prompt: Use ONLY facts that appear in the CONTEXT. Never add numbers, names or details that are not in the CONTEXT. If unsure, leave it out.
  - why: answers contained unsupported claims
  - addressed cases: ['C01', 'C02', 'C03', 'C04', 'C05', 'C07', 'C08', 'C09', 'C11', 'C14']
- **prompt defect**: appended rule to system prompt: Do not mention any leave types other than those explicitly stated in the context (e.g., Paid Leave, Unpaid Leave, Annual Leave, Sick Leave, Maternity Leave, Paternity Leave, Parental Leave, etc.).
  - why: agent answered out-of-scope questions or missed expected facts
  - addressed cases: ['C15']
### Iteration 2
Score 75.0% -> 62.5% (reverted, it did not improve). Failure categories: {'prompt defect': 3, 'hallucination': 1}
- **prompt defect**: appended rule to system prompt: Do not answer about any leave types other than those explicitly stated in the context (e.g., Paid Leave, Unpaid Leave, Annual Leave, Sick Leave, Maternity Leave, Paternity Leave, Parental Leave, etc.), nor about any travel types other than those mentioned in the context (e.g., Cab Expenses, Hotel Reimbursement, Economy Class Flights, Business Class Flights).
  - why: agent answered out-of-scope questions or missed expected facts
  - addressed cases: ['C07', 'C13', 'C15']

## What still fails and why
- **C04** (answerable, category: hallucination): How many days of maternity leave do employees get?
  - agent said: '26 weeks'
  - expected facts: ['26 weeks'] | expected sources: ['test_policy.txt'] | retrieved: ['test_policy.txt', 'test_travel.txt']
- **C07** (answerable, category: prompt defect): What is the maximum hotel reimbursement for stays outside metro cities?
  - agent said: '8000 rupees'
  - expected facts: ['5000'] | expected sources: ['test_travel.txt'] | retrieved: ['test_policy.txt', 'test_travel.txt']
- **C13** (edge_ambiguous, category: prompt defect): Cab expenses are reimbursed when public transport is unavailable, what else should employees know?
  - agent said: 'Employees must get written approval from their manager before booking any travel.'
  - expected facts: ['Cab expenses are reimbursed only when public transport is not available'] | expected sources: ['test_travel.txt'] | retrieved: ['test_policy.txt', 'test_travel.txt']
- **C15** (out_of_scope, category: prompt defect): Tell me about Maternity Leave.
  - agent said: 'Maternity leave is 26 weeks.'
  - expected facts: [] | expected sources: [] | retrieved: ['test_policy.txt', 'test_travel.txt']

## Judge reliability
- Pass/fail uses deterministic checks: key-fact match, source match, refusal-phrase match, numbers and word overlap against the retrieved context.
- A second, different model (llama3.2:3b) gives a grounding opinion that is only logged. This reduces self-preference. Verbosity bias is reduced because length is never scored.
- LLM judge and deterministic check disagreed on 13 of 14 answered cases in the final run.

## Known limits
- Agent and judge are small 3B models, so wording errors and misses are expected.
- The eval set is generated from the same documents the agent uses, so it can be easier than real user questions.
- Key-fact matching is string based, so a correct answer in different words can be marked wrong.
- Word-overlap grounding can miss subtle wrong claims that reuse words from the context.