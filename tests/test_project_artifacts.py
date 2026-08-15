from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "project_artifacts", ROOT / "scripts" / "project_artifacts.py"
)
assert SPEC and SPEC.loader
project_artifacts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(project_artifacts)


class ProjectArtifactsTests(unittest.TestCase):
    def test_initialize_creates_expected_files_without_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            project_artifacts.initialize(project, "Projet test", "projet-test")
            conception = project / "conception"
            expected = {
                "journal.md",
                "decisions.json",
                "sources.md",
                "specification.md",
                "tours",
                "planning",
            }
            self.assertEqual(expected, {path.name for path in conception.iterdir()})
            journal = conception / "journal.md"
            journal.write_text("contenu utilisateur\n", encoding="utf-8")
            project_artifacts.initialize(project, "Projet test", "projet-test")
            self.assertEqual("contenu utilisateur\n", journal.read_text(encoding="utf-8"))

    def test_archive_is_versioned_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project_artifacts.initialize(project, "Projet test", "projet-test")
            questionnaire = root / "questionnaire.html"
            questionnaire.write_text("<!doctype html><title>Test</title>", encoding="utf-8")
            answers = root / "answers.json"
            answers.write_text(
                json.dumps({"schema": "project-workshop-answers-v2", "answers": {}}),
                encoding="utf-8",
            )

            project_artifacts.archive_round(project, "T01", questionnaire, [answers])
            archive = project / "conception" / "tours" / "T01"
            self.assertTrue((archive / "questionnaire.html").is_file())
            manifest = json.loads((archive / "archive.json").read_text(encoding="utf-8"))
            self.assertEqual("project-workshop-round-archive-v2", manifest["schema"])
            self.assertEqual(2, len(manifest["files"]))
            with self.assertRaises(project_artifacts.ArtifactError):
                project_artifacts.archive_round(project, "T01", questionnaire, [answers])

    def test_validate_empty_register_and_reject_unknown_superseded_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "decisions.json"
            path.write_text(
                json.dumps(
                    {
                        "schema": "project-workshop-decisions-v2",
                        "project": {"title": "Test", "slug": "test"},
                        "updated_at": None,
                        "decisions": [],
                    }
                ),
                encoding="utf-8",
            )
            project_artifacts.validate_decisions(path)

            data = json.loads(path.read_text(encoding="utf-8"))
            data["decisions"].append(
                {
                    "id": "D-001",
                    "kind": "decision",
                    "status": "accepted",
                    "title": "Décision",
                    "rationale": "Raison",
                    "source_round": "T01",
                    "source_questions": ["Q01"],
                    "evidence": ["Export T01"],
                    "confidence": "high",
                    "owner": None,
                    "priority": "important",
                    "supersedes": ["D-999"],
                    "created_at": "2026-08-16",
                    "updated_at": "2026-08-16",
                }
            )
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(project_artifacts.ArtifactError):
                project_artifacts.validate_decisions(path)

    def test_decision_register_contract_is_strict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "decisions.json"
            base = {
                "id": "D-001",
                "kind": "decision",
                "status": "accepted",
                "title": "Décision",
                "rationale": "Raison",
                "source_round": "T01",
                "source_questions": ["Q01"],
                "evidence": ["Export T01"],
                "confidence": "high",
                "owner": None,
                "priority": "important",
                "supersedes": [],
                "created_at": "2026-08-16",
                "updated_at": "2026-08-16",
            }
            root = {
                "schema": "project-workshop-decisions-v2",
                "project": {"title": "Test", "slug": "test"},
                "updated_at": "2026-08-16",
                "decisions": [base],
            }
            for mutate in (
                lambda value: value["decisions"][0].pop("owner"),
                lambda value: value["decisions"][0].update({"unexpected": True}),
                lambda value: value["decisions"][0].update({"source_questions": ["bad id"]}),
            ):
                data = json.loads(json.dumps(root))
                mutate(data)
                path.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaises(project_artifacts.ArtifactError):
                    project_artifacts.validate_decisions(path)


if __name__ == "__main__":
    unittest.main()
