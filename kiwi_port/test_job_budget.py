import subprocess
import unittest
from pathlib import Path


class JobBudgetTests(unittest.TestCase):
    def budget(self, elapsed, requested=270):
        result = subprocess.run(["python3", str(Path(__file__).with_name("job_budget.py")), "--elapsed-seconds", str(elapsed), "--requested-minutes", str(requested)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return int(result.stdout)

    def test_normal_setup_allows_long_compile(self):
        self.assertEqual(self.budget(20 * 60), 270 * 60)

    def test_slow_setup_preserves_checkpoint_reserve(self):
        self.assertEqual(self.budget(120 * 60), (350 - 120 - 45) * 60)

    def test_no_time_remaining_refuses_compile(self):
        result = subprocess.run(["python3", str(Path(__file__).with_name("job_budget.py")), "--elapsed-seconds", str(310 * 60)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("checkpoint", result.stderr)

    def test_explicit_smaller_budget_is_honored(self):
        self.assertEqual(self.budget(0, 90), 90 * 60)
