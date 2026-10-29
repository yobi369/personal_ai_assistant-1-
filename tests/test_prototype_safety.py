from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "personal_ai_assistant (1).html"
README = ROOT / "README.md"
SECURITY = ROOT / "SECURITY.md"
READINESS = ROOT / "docs" / "PRODUCTION_READINESS.md"

class PrototypeSafetyChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML.read_text(encoding="utf-8")
        cls.readme = README.read_text(encoding="utf-8")
        cls.security = SECURITY.read_text(encoding="utf-8")
        cls.readiness = READINESS.read_text(encoding="utf-8")

    def test_prototype_is_clearly_labelled(self):
        self.assertIn("Prototype mode:", self.html)
        self.assertIn("illustrative demo content", self.html)
        self.assertIn("Do not enter sensitive information", self.html)

    def test_chat_is_not_presented_as_a_real_model(self):
        self.assertIn("canned examples, not AI-generated answers", self.html)
        self.assertIn("No real documents are connected", self.html)

    def test_unverified_privacy_guarantees_are_not_claimed(self):
        self.assertNotIn("100% Local Processing", self.html)
        self.assertNotIn("Zero Cloud Data", self.html)
        self.assertNotIn("Zero data transmission to external servers", self.html)
        self.assertIn("not implemented or verified", self.html)

    def test_fake_live_metric_mutation_is_absent(self):
        self.assertNotIn("setInterval(", self.html)
        self.assertIn("static illustrative sample values", self.html)

    def test_release_limitations_are_documented(self):
        self.assertIn("NOT READY", self.readiness)
        self.assertIn("not certified production-ready", self.readme.lower())
        self.assertIn("least privilege", self.security.lower())

if __name__ == "__main__":
    unittest.main(verbosity=2)
