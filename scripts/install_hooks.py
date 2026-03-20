"""Install local git hooks from scripts/ into .git/hooks/."""

import shutil
import stat
from pathlib import Path

hook_src = Path("scripts/post-commit")
hook_dst = Path(".git/hooks/post-commit")

shutil.copy2(hook_src, hook_dst)
hook_dst.chmod(hook_dst.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
print("[install-hooks] post-commit hook installed.")
