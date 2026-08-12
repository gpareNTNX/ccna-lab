import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class DeploymentTests(unittest.TestCase):
    def test_version_exists(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")

    def test_windows_files(self):
        for rel in [
            "deploy/windows/build-portable.ps1",
            "deploy/windows/build-installer.ps1",
            "deploy/windows/installer.iss",
        ]:
            self.assertTrue((ROOT / rel).exists(), rel)

    def test_macos_files(self):
        for rel in [
            "deploy/macos/build-app.sh",
            "deploy/macos/package-dmg.sh",
            "deploy/macos/notarize-dmg.sh",
        ]:
            self.assertTrue((ROOT / rel).exists(), rel)

    def test_images_are_gitignored(self):
        content = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("*.qcow2", content)
        self.assertIn("*.iso", content)

if __name__ == "__main__":
    unittest.main()
