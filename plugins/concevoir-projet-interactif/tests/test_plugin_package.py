from __future__ import annotations

import json
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PLUGIN_ROOT.parents[1]
MANIFEST = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
MARKETPLACE = REPOSITORY_ROOT / ".agents" / "plugins" / "marketplace.json"


class PluginPackageTests(unittest.TestCase):
    def test_manifest_points_to_the_bundled_skill_and_assets(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("concevoir-projet-interactif", manifest["name"])
        self.assertEqual("1.0.0", manifest["version"])
        self.assertEqual("./skills/", manifest["skills"])

        skill = PLUGIN_ROOT / "skills" / manifest["name"] / "SKILL.md"
        self.assertTrue(skill.is_file())

        interface = manifest["interface"]
        asset_paths = [
            interface["composerIcon"],
            interface["logo"],
            *interface["screenshots"],
        ]
        for relative_path in asset_paths:
            with self.subTest(relative_path=relative_path):
                self.assertTrue((PLUGIN_ROOT / relative_path).resolve().is_file())

    def test_public_marketplace_points_to_the_plugin(self) -> None:
        marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        self.assertEqual("nettyks", marketplace["name"])
        entry = next(
            plugin
            for plugin in marketplace["plugins"]
            if plugin["name"] == "concevoir-projet-interactif"
        )
        self.assertEqual(
            "./plugins/concevoir-projet-interactif", entry["source"]["path"]
        )
        self.assertEqual("AVAILABLE", entry["policy"]["installation"])
        self.assertEqual("ON_INSTALL", entry["policy"]["authentication"])


if __name__ == "__main__":
    unittest.main()
