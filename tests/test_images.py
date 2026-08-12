import unittest
from pathlib import Path
import tempfile
from ccna_lab_builder.core.images import detect_image

class ImageTests(unittest.TestCase):
    def test_iosv(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "vios-adventerprisek9-m.spa.159-3.m6.qcow2"
            p.write_bytes(b"x")
            info = detect_image(p)
            self.assertEqual(info["template"], "vios")
            self.assertTrue(info["folder"].startswith("vios-"))

    def test_iosvl2(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "vios_l2-adventerprisek9.qcow2"
            p.write_bytes(b"x")
            info = detect_image(p)
            self.assertEqual(info["template"], "viosl2")
            self.assertTrue(info["folder"].startswith("viosl2-"))

if __name__ == "__main__":
    unittest.main()
