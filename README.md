# claude_api

Notebook for the Anthropic Academy "Building with the Claude API" course.

## After cloning

Notebook outputs are stripped on commit by a git clean filter. The filter
config lives in `.git/config`, so re-create it in a fresh clone:

```
git config filter.strip-outputs.clean "python tools/strip_outputs.py"
```

(Use an absolute interpreter path if `python` isn't on git's PATH. It needs `nbformat`.)
