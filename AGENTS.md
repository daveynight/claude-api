# Building with the Codex API

Anthropic Academy course notebook, worked through lesson by lesson. It is also where we build tooling meant to be reused in other projects.

## Layout
- `claude_api.ipynb`: course notebook, one `### Lnn:` heading per lesson. Keep cells thin.
- `prompt_evaluator.py`: reusable `PromptEvaluator` (dataset generation, model-graded evals, HTML report). Not part of the course files; we wrote it for L15.
- `dataset.json`: AWS task dataset used by L11-L14. Don't overwrite it. L15 uses `meal_dataset.json`.
- `.env`: `ANTHROPIC_API_KEY`, loaded with `python-dotenv`. Never commit it.

## Conventions
- Anything reusable goes in an importable `.py` module with no notebook dependencies. Notebook cells only call it.
- Use sync code with `ThreadPoolExecutor` for concurrency, not asyncio. Notebooks already run an event loop.
- Eval and grading calls use Haiku (`Codex-haiku-4-5`); the lesson chat examples use Sonnet.
- Ask for JSON with the prefill `"```json"` plus stop sequence `"```"`, then `json.loads`.
- Generated artifacts (`output.html`, `meal_dataset.json`) are outputs, not source.

## Secrets
- `tools/git-hooks/pre-commit` blocks staged `.env`/key files and secret-looking strings (it prints file names only). It is active via `git config core.hooksPath tools/git-hooks`; that setting is per-clone, so re-run it after cloning.
