# Gemini / Antigravity Assistant Guide

This repository uses Antigravity (Gemini) as its primary agentic coding assistant. 

Unlike traditional setups that might rely on a `claude.md` or `.cursorrules` file at the root of the project, Antigravity discovers context, rules, and skills through the **Customizations Framework**.

## Where to Find Agent Instructions
The core behavioral rules and instructions for this repository are located in:
- `@[.agents/AGENTS.md]` (Workspace Customizations Root)

## How It Works
- **Rules**: Global and project-scoped rules are appended to `AGENTS.md`. The agent automatically reads these rules and applies them to every task (e.g., running pre-commit hooks, auto-fixing tests, keeping documentation in sync).
- **Skills**: Specialized actions are stored in `.agents/skills/`. Each skill has a `SKILL.md` that is dynamically triggered based on the task context.
- **Knowledge Items (KIs)**: We maintain architectural patterns and summaries in the `.gemini/knowledge` directory to prevent redundant research.

When instructing the agent, refer to `AGENTS.md` if you want to update its default behavior or persona.
