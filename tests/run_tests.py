"""
tests/run_tests.py - Runner de testes unitarios (sem dependencias externas)

Uso:
    python tests/run_tests.py
    python tests/run_tests.py -v           # verbose
    python tests/run_tests.py test_storage # modulo especifico
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def run(verbosity: int = 1, pattern: str = "test*.py"):
    loader = unittest.TestLoader()
    suite  = loader.discover(
        start_dir = str(Path(__file__).parent),
        pattern   = pattern,
    )
    runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    verbose  = "-v" in sys.argv
    pattern  = next((a for a in sys.argv[1:] if not a.startswith("-")), "test*.py")
    if not pattern.endswith(".py"):
        pattern = f"{pattern}.py"
    sys.exit(run(verbosity=2 if verbose else 1, pattern=pattern))
