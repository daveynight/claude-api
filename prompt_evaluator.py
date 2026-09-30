"""PromptEvaluator: generate a test dataset from a task description, run a
prompt function over it, grade each output with a model, and write an HTML report.

Everything is synchronous and fans out with a thread pool, so it works inside a
notebook (which already owns an event loop) without asyncio tricks.
"""
import html
import json
from concurrent.futures import ThreadPoolExecutor
from statistics import mean

from anthropic import Anthropic

PASS_THRESHOLD = 7


class PromptEvaluator:
    def __init__(self, max_concurrent_tasks=3, model="claude-haiku-4-5", client=None):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.model = model
        self.client = client or Anthropic()

    # ---- helpers ---------------------------------------------------------

    def _ask_json(self, prompt, max_tokens=2000):
        """Prefill "```json" and stop on "```" so the reply is bare JSON."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": "```json"},
            ],
            stop_sequences=["```"],
        )
        return json.loads(message.content[0].text)

    def _map(self, fn, items):
        with ThreadPoolExecutor(max_workers=self.max_concurrent_tasks) as pool:
            return list(pool.map(fn, items))

    # ---- dataset generation ---------------------------------------------

    def generate_dataset(self, task_description, prompt_inputs_spec, output_file, num_cases=3):
        """Two steps: brainstorm `num_cases` distinct scenarios, then expand each
        into concrete prompt inputs plus the criteria a good answer must meet."""
        spec_text = "\n".join(f'- "{k}": {v}' for k, v in prompt_inputs_spec.items())

        ideas = self._ask_json(f"""
Task the prompt under test must perform: {task_description}

Brainstorm {num_cases} distinct, realistic test scenarios for this task. Cover a
spread of typical cases and tricky edge cases (unusual inputs, conflicting
constraints, restrictions that rule out common answers).

Respond with a JSON array of {num_cases} short strings, one scenario each.
""")[:num_cases]

        def expand(idea):
            case = self._ask_json(f"""
Task the prompt under test must perform: {task_description}

Scenario: {idea}

Write one test case for this scenario. The prompt takes these inputs:
{spec_text}

Respond with a JSON object with exactly these keys:
- "scenario": the scenario description, one sentence
- "prompt_inputs": an object with a realistic string value for each input above ({", ".join(prompt_inputs_spec)})
- "solution_criteria": an array of 4-6 specific, checkable requirements a good answer must meet
""")
            case["prompt_inputs"] = {k: str(case["prompt_inputs"].get(k, "")) for k in prompt_inputs_spec}
            return case

        dataset = self._map(expand, ideas)
        with open(output_file, "w") as f:
            json.dump(dataset, f, indent=2)
        return dataset

    # ---- evaluation ------------------------------------------------------

    def _grade(self, test_case, output, extra_criteria):
        criteria = "\n".join(f"- {c}" for c in test_case["solution_criteria"])
        extra = f"\nAdditional criteria that also apply:\n{extra_criteria}\n" if extra_criteria else ""
        return self._ask_json(f"""
You are a strict evaluator of AI-generated answers.

Scenario: {test_case["scenario"]}
Inputs: {json.dumps(test_case["prompt_inputs"])}

Solution criteria:
{criteria}
{extra}
Answer being evaluated:
<answer>
{output}
</answer>

Judge the answer against every criterion. Respond with a JSON object with:
- "reasoning": 2-3 sentences explaining the score, naming what is missing or wrong
- "score": an integer 1-10 (10 = meets every criterion, 1 = ignores the task)
""")

    def run_evaluation(self, run_prompt_function, dataset_file, extra_criteria=None,
                       html_output_file="output.html"):
        with open(dataset_file) as f:
            dataset = json.load(f)

        def run_case(test_case):
            output = run_prompt_function(test_case["prompt_inputs"])
            grade = self._grade(test_case, output, extra_criteria)
            return {
                "test_case": test_case,
                "output": output,
                "score": grade["score"],
                "reasoning": grade["reasoning"],
            }

        results = self._map(run_case, dataset)
        average = mean(r["score"] for r in results)
        pass_rate = 100 * sum(r["score"] >= PASS_THRESHOLD for r in results) / len(results)
        print(f"Average score: {average:.1f} / 10   Pass rate (>={PASS_THRESHOLD}): {pass_rate:.1f}%")

        with open(html_output_file, "w") as f:
            f.write(self._render_report(results, average, pass_rate))
        print(f"Report written to {html_output_file}")
        return results

    # ---- report ----------------------------------------------------------

    @staticmethod
    def _render_report(results, average, pass_rate):
        e = html.escape
        rows = []
        for r in results:
            tc = r["test_case"]
            inputs = "<br>".join(f"<b>{e(k)}:</b> {e(v)}" for k, v in tc["prompt_inputs"].items())
            criteria = "".join(f"<li>{e(c)}</li>" for c in tc["solution_criteria"])
            band = "good" if r["score"] >= PASS_THRESHOLD else "mid" if r["score"] >= 5 else "bad"
            rows.append(f"""
<tr>
  <td>{e(tc["scenario"])}</td>
  <td>{inputs}</td>
  <td><ul>{criteria}</ul></td>
  <td><pre>{e(r["output"])}</pre></td>
  <td><span class="score {band}">{e(str(r["score"]))}</span></td>
  <td>{e(r["reasoning"])}</td>
</tr>""")

        return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Prompt Evaluation Report</title>
<style>
  body {{ font-family: -apple-system, Helvetica, Arial, sans-serif; margin: 0; background: #eee; color: #222; }}
  h1 {{ margin: 40px 10px 20px; }}
  .stats {{ display: flex; gap: 48px; padding: 0 10px 24px; }}
  .stat {{ flex: 1; background: #fff; padding: 16px; border-radius: 4px; box-shadow: 0 1px 3px #0002; }}
  .stat .label {{ color: #555; }} .stat .value {{ font-size: 24px; font-weight: 600; margin-top: 8px; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; }}
  th {{ background: #333; color: #fff; text-align: left; padding: 12px 4px; }}
  td {{ vertical-align: top; padding: 12px 4px; border-bottom: 1px solid #ddd; line-height: 1.4; }}
  ul {{ margin: 0; padding-left: 16px; }}
  pre {{ margin: 0; white-space: pre-wrap; background: #f4f4f4; border: 1px solid #ddd;
        border-radius: 4px; padding: 8px; font-size: 13px; }}
  .score {{ display: inline-block; min-width: 28px; text-align: center; padding: 6px; border-radius: 4px; font-weight: 600; }}
  .good {{ background: #c8f0d0; color: #17652b; }} .mid {{ background: #fdeeb4; color: #8a6100; }}
  .bad {{ background: #f8cfd2; color: #a3202a; }}
</style></head><body>
<h1>Prompt Evaluation Report</h1>
<div class="stats">
  <div class="stat"><div class="label">Total Test Cases</div><div class="value">{len(results)}</div></div>
  <div class="stat"><div class="label">Average Score</div><div class="value">{average:.1f} / 10</div></div>
  <div class="stat"><div class="label">Pass Rate (&ge;{PASS_THRESHOLD})</div><div class="value">{pass_rate:.1f}%</div></div>
</div>
<table>
<tr><th>Scenario</th><th>Prompt Inputs</th><th>Solution Criteria</th><th>Output</th><th>Score</th><th>Reasoning</th></tr>
{"".join(rows)}
</table></body></html>"""
