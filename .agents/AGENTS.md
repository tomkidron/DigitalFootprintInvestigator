# Custom Rules & Persona

## About Me
Senior QA Engineer. Can read and understand code but not a developer. Relies heavily on AI/LLMs and is into vibe coding. Tailor suggestions accordingly - focus on outcomes, not implementation minutiae.

## Communication
Be concise and straight to the point. No filler, no preamble.

## Auto-fix Loop
After making any code changes, run the relevant tests. If tests fail, fix the issue and re-run before stopping. Do not stop with a known failing test unless explicitly told to.

## Pre-commit & Verification
Always run pre-commit hooks before committing. Never skip them with `--no-verify`.

Pre-commit hooks are the source of truth for code quality. Trust them for:
*   Import errors and linting
*   Security scanning (Bandit, secret detection)

If a hook fails, fix the underlying issue before retrying. Do not work around hook failures.
