import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import bump_versions


class CacheVersionTests(unittest.TestCase):
    def test_adds_and_updates_local_import_hashes_without_touching_vendor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "js" / "vendor").mkdir(parents=True)
            dependency = root / "js" / "model.js"
            dependency.write_text("export const value = 1;\n")
            vendor = root / "js" / "vendor" / "three.js"
            vendor.write_text("export const vendor = true;\n")
            module = root / "js" / "app.js"
            module.write_text("import { value } from './model.js';\n"
                              "import './vendor/three.js';\n"
                              "const lazy = () => import('./model.js');\n")
            page = root / "index.html"
            page.write_text('<script src="js/app.js?v=old"></script>')
            with patch.object(bump_versions, "ROOT", root):
                self.assertTrue(bump_versions.rewrite(check=True))
                self.assertNotIn("?v=", module.read_text())
                bump_versions.rewrite(check=False)
                self.assertIn(f"./model.js?v={bump_versions.digest(dependency)}", module.read_text())
                self.assertIn("'./vendor/three.js'", module.read_text())
                self.assertIn(f"js/app.js?v={bump_versions.digest(module)}", page.read_text())
                self.assertFalse(bump_versions.rewrite(check=True))
                dependency.write_text("export const value = 2;\n")
                self.assertTrue(bump_versions.rewrite(check=True))
                bump_versions.rewrite(check=False)
                self.assertFalse(bump_versions.rewrite(check=True))


if __name__ == "__main__":
    unittest.main()
