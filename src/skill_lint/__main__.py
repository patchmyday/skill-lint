"""Allow running as `python -m skill_lint`."""

from skill_lint.cli import main
import sys

sys.exit(main())
