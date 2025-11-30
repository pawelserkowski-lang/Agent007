import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from launcher import _build_pythonpath, build_launch_command, launch_app


class BuildLaunchCommandTests(unittest.TestCase):
    def test_returns_command_with_explicit_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "main.py").write_text("print('ok')\n", encoding="utf-8")

            cmd = build_launch_command(tmp_path, python_executable="python3")

            self.assertEqual(cmd, ["python3", str(tmp_path / "main.py")])

    def test_missing_main_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                build_launch_command(Path(tmp), python_executable="python3")


class LaunchAppTests(unittest.TestCase):
    def test_runs_subprocess_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            main_path = tmp_path / "main.py"
            # This script simply exits successfully.
            main_path.write_text("print('launched')\n", encoding="utf-8")

            calls = []

            def fake_run(command, cwd, env, check):
                calls.append((tuple(command), Path(cwd), env.get("PYTHONPATH"), check))
                # Emulate subprocess.run success
                return subprocess.CompletedProcess(command, 0)

            # Patch subprocess.run
            original_run = subprocess.run
            subprocess.run = fake_run
            try:
                launch_app(command=[sys.executable, str(main_path)], repo_root=tmp_path)
            finally:
                subprocess.run = original_run

            self.assertEqual(len(calls), 1)
            recorded_command, recorded_cwd, recorded_pythonpath, recorded_check = calls[0]
            self.assertEqual(recorded_command, (sys.executable, str(main_path)))
            self.assertEqual(recorded_cwd, tmp_path)
            self.assertEqual(recorded_pythonpath, str(tmp_path))
            self.assertTrue(recorded_check)

    def test_preserves_existing_pythonpath(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            main_path = tmp_path / "main.py"
            main_path.write_text("print('launched')\n", encoding="utf-8")

            calls = []

            def fake_run(command, cwd, env, check):
                calls.append(env.get("PYTHONPATH"))
                return subprocess.CompletedProcess(command, 0)

            original_run = subprocess.run
            subprocess.run = fake_run
            original_pythonpath = os.environ.get("PYTHONPATH")
            os.environ["PYTHONPATH"] = "/existing/path"
            try:
                launch_app(command=[sys.executable, str(main_path)], repo_root=tmp_path)
            finally:
                subprocess.run = original_run
                if original_pythonpath is None:
                    os.environ.pop("PYTHONPATH", None)
                else:
                    os.environ["PYTHONPATH"] = original_pythonpath

            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0], f"{tmp_path}{os.pathsep}/existing/path")

    def test_deduplicates_repo_root(self):
        repo = Path("/repo/root")
        existing = f"{repo}{os.pathsep}/existing"

        result = _build_pythonpath(repo, existing)

        self.assertEqual(result, f"{repo}{os.pathsep}/existing")

    def test_filters_empty_components(self):
        repo = Path("/repo/root")
        existing = f":/first::{os.pathsep}/second/"

        result = _build_pythonpath(repo, existing)

        self.assertEqual(result, f"{repo}{os.pathsep}/first{os.pathsep}/second/")


if __name__ == "__main__":
    unittest.main()
