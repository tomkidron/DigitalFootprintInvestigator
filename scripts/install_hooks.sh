#!/bin/sh
# Install local git hooks from scripts/ into .git/hooks/
cp scripts/post-commit .git/hooks/post-commit
chmod +x .git/hooks/post-commit
echo "[install-hooks] post-commit hook installed."
