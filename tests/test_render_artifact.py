from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "render_artifact.py"
SPEC = importlib.util.spec_from_file_location("render_artifact", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
render_artifact = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(render_artifact)


def choice(
    choice_id: str,
    label: str,
    tone: str = "neutral",
    needs_clarification: bool = False,
) -> dict[str, object]:
    return {
        "id": choice_id,
        "label": label,
        "tone": tone,
        "needs_clarification": needs_clarification,
    }


def valid_questionnaire() -> dict[str, object]:
    return {
        "schema": "project-workshop-questionnaire-v2",
        "project": {
            "title": "Atelier de quartier",
            "slug": "atelier-quartier",
            "subtitle": "Tour de cadrage",
        },
        "round_id": "TourOrientation",
        "round": "Tour 1 — Orientation",
        "storage_key": "atelier-quartier-tour-1-v2",
        "intro_title": "Commençons par l’usage",
        "intro": "Les réponses de ce tour préciseront le besoin.",
        "theme": {
            "bg": "#f3efe8",
            "primary": "#315f52",
            "focus": "#c66a32",
            "radius": "20px",
        },
        "sections": [
            {
                "id": "Orientation",
                "title": "Orientation",
                "questions": [
                    {
                        "id": "QOpen",
                        "type": "open",
                        "title": "Quel résultat recherchez-vous ?",
                        "answer_placeholder": "Décrivez le résultat attendu",
                        "allow_note": False,
                    },
                    {
                        "id": "QDecision",
                        "type": "decision",
                        "title": "Le service doit-il être public ?",
                        "allow_note": True,
                    },
                    {
                        "id": "QSingle",
                        "type": "single_choice",
                        "title": "Qui l’utilisera en premier ?",
                        "choices": [
                            choice("Personnel", "Une personne"),
                            choice("Equipe", "Une équipe"),
                        ],
                    },
                    {
                        "id": "QMulti",
                        "type": "multi_choice",
                        "title": "Quels supports sont nécessaires ?",
                        "choices": [
                            choice("Web", "Navigateur"),
                            choice("Mobile", "Mobile"),
                        ],
                    },
                    {
                        "id": "QScale",
                        "type": "scale",
                        "title": "Quel niveau d’autonomie viser ?",
                        "scale": {
                            "min": 1,
                            "max": 5,
                            "step": 1,
                            "default": 3,
                            "min_label": "Faible",
                            "max_label": "Fort",
                        },
                    },
                    {
                        "id": "QRanking",
                        "type": "ranking",
                        "title": "Classez les priorités",
                        "choices": [
                            choice("Simplicite", "Simplicité"),
                            choice("Vitesse", "Vitesse"),
                        ],
                    },
                ],
            }
        ],
    }


def segment(
    segment_id: str,
    title: str,
    phase: str,
    order: int,
    dependencies: list[str],
) -> dict[str, object]:
    return {
        "id": segment_id,
        "title": title,
        "objective": f"Obtenir un résultat vérifiable pour {title.lower()}.",
        "phase": phase,
        "status": "APlanifier",
        "order": order,
        "dependencies": dependencies,
        "decision_refs": [f"Decision{segment_id}"],
        "deliverables": [f"Livrable {segment_id}"],
        "acceptance": [f"Critère vérifiable {segment_id}"],
        "prerequisites": [],
        "risks": [],
        "questions": [],
    }


def valid_planning() -> dict[str, object]:
    return {
        "schema": "project-workshop-planning-v2",
        "project": {
            "title": "Atelier de quartier",
            "slug": "atelier-quartier",
            "subtitle": "Plan de réalisation",
        },
        "storage_key": "atelier-quartier-plan-v2",
        "view": "roadmap",
        "theme": {"bg": "#edf2ef", "primary": "#245d4d"},
        "phases": [
            {
                "id": "Preuve",
                "title": "Prouver l’usage",
                "order": 1,
                "milestone": "Le parcours principal est compris",
            },
            {
                "id": "Ouverture",
                "title": "Préparer l’ouverture",
                "order": 2,
            },
        ],
        "columns": [
            {"id": "APlanifier", "title": "À planifier"},
            {"id": "Termine", "title": "Terminé"},
        ],
        "open_questions": [
            {
                "id": "SupportOwner",
                "text": "Qui assurera le support ?",
                "severity": "avant-segment",
                "segment": "S3",
            }
        ],
        "segments": [
            segment("S1", "Valider le besoin", "Preuve", 1, []),
            segment("S2", "Tester le parcours", "Preuve", 2, ["S1"]),
            {
                **segment("S3", "Préparer le service", "Ouverture", 1, ["S2"]),
                "summary": "Rendre le service prêt pour son premier public.",
                "owner": "Équipe produit",
                "effort": 5,
                "priority": "haute",
            },
        ],
    }


class QuestionnaireValidationTests(unittest.TestCase):
    def test_valid_questionnaire_covers_all_question_types(self) -> None:
        render_artifact.validate_questionnaire(valid_questionnaire())

    def test_questionnaire_locale_accepts_english_and_rejects_unknown_values(self) -> None:
        english = valid_questionnaire()
        english["locale"] = "en"
        render_artifact.validate_questionnaire(english)
        normalized = render_artifact.normalized_for_render("questionnaire", english)
        decision = normalized["sections"][0]["questions"][1]
        self.assertEqual([item["label"] for item in decision["choices"]], ["Yes", "No", "Maybe"])

        invalid = valid_questionnaire()
        invalid["locale"] = "de"
        with self.assertRaisesRegex(render_artifact.ConfigError, "fr ou en"):
            render_artifact.validate_questionnaire(invalid)

    def test_scalar_section_is_a_clean_config_error(self) -> None:
        data = valid_questionnaire()
        data["sections"] = ["invalide"]
        with self.assertRaisesRegex(render_artifact.ConfigError, "objet JSON"):
            render_artifact.validate_questionnaire(data)

    def test_question_identifier_must_be_safe(self) -> None:
        data = valid_questionnaire()
        data["sections"][0]["questions"][0]["id"] = "__proto__"
        with self.assertRaisesRegex(render_artifact.ConfigError, "doit respecter"):
            render_artifact.validate_questionnaire(data)

    def test_open_question_forbids_choices(self) -> None:
        data = valid_questionnaire()
        data["sections"][0]["questions"][0]["choices"] = [
            choice("Oui", "Oui"),
            choice("Non", "Non"),
        ]
        with self.assertRaisesRegex(render_artifact.ConfigError, "interdit"):
            render_artifact.validate_questionnaire(data)

    def test_non_open_question_requires_two_choices(self) -> None:
        data = valid_questionnaire()
        data["sections"][0]["questions"][1]["choices"] = [
            choice("Oui", "Oui")
        ]
        with self.assertRaisesRegex(render_artifact.ConfigError, "au moins deux"):
            render_artifact.validate_questionnaire(data)

    def test_choice_contract_is_strict(self) -> None:
        data = valid_questionnaire()
        data["sections"][0]["questions"][2]["choices"][0]["tone"] = "maybe"
        with self.assertRaisesRegex(render_artifact.ConfigError, "neutral"):
            render_artifact.validate_questionnaire(data)

    def test_decision_without_choices_receives_default_trio_for_rendering(self) -> None:
        data = valid_questionnaire()
        render_artifact.validate_questionnaire(data)
        normalized = render_artifact.normalized_for_render("questionnaire", data)
        decision = normalized["sections"][0]["questions"][1]
        self.assertEqual([item["id"] for item in decision["choices"]], ["yes", "no", "maybe"])
        self.assertTrue(decision["choices"][2]["needs_clarification"])
        self.assertNotIn("choices", data["sections"][0]["questions"][1])

    def test_scale_requires_numeric_contract_and_forbids_choices(self) -> None:
        missing = valid_questionnaire()
        del missing["sections"][0]["questions"][4]["scale"]["step"]
        with self.assertRaisesRegex(render_artifact.ConfigError, "manquante"):
            render_artifact.validate_questionnaire(missing)

        choices = valid_questionnaire()
        choices["sections"][0]["questions"][4]["choices"] = [
            choice("Faible", "Faible"),
            choice("Fort", "Fort"),
        ]
        with self.assertRaisesRegex(render_artifact.ConfigError, "interdit"):
            render_artifact.validate_questionnaire(choices)

    def test_theme_rejects_unknown_keys_and_urls(self) -> None:
        for theme, expected in (
            ({"unknown": "#fff"}, "inconnue"),
            ({"bg": "url(https://example.test/pixel)"}, "aucune URL"),
        ):
            with self.subTest(theme=theme):
                data = valid_questionnaire()
                data["theme"] = theme
                with self.assertRaisesRegex(render_artifact.ConfigError, expected):
                    render_artifact.validate_questionnaire(data)


class PlanningValidationTests(unittest.TestCase):
    def test_valid_planning(self) -> None:
        data = valid_planning()
        render_artifact.validate_planning(data)
        normalized = render_artifact.normalized_for_render("planning", data)
        self.assertEqual(normalized["segments"][0]["summary"], normalized["segments"][0]["objective"])
        self.assertEqual(
            normalized["segments"][2]["summary"],
            "Rendre le service prêt pour son premier public.",
        )

    def test_planning_locale_accepts_english_and_rejects_unknown_values(self) -> None:
        english = valid_planning()
        english["locale"] = "en"
        render_artifact.validate_planning(english)

        invalid = valid_planning()
        invalid["locale"] = "es"
        with self.assertRaisesRegex(render_artifact.ConfigError, "fr ou en"):
            render_artifact.validate_planning(invalid)

    def test_scalar_segment_is_a_clean_config_error(self) -> None:
        data = valid_planning()
        data["segments"] = ["invalide"]
        with self.assertRaisesRegex(render_artifact.ConfigError, "objet JSON"):
            render_artifact.validate_planning(data)

    def test_required_deliverables_and_acceptance_are_non_empty(self) -> None:
        for key in ("decision_refs", "deliverables", "acceptance"):
            with self.subTest(key=key):
                data = valid_planning()
                data["segments"][0][key] = []
                with self.assertRaisesRegex(render_artifact.ConfigError, "non vide"):
                    render_artifact.validate_planning(data)

    def test_phase_and_status_must_exist(self) -> None:
        for key, value, expected in (
            ("phase", "Absente", "Phase inconnue"),
            ("status", "Inconnu", "Statut inconnu"),
        ):
            with self.subTest(key=key):
                data = valid_planning()
                data["segments"][0][key] = value
                with self.assertRaisesRegex(render_artifact.ConfigError, expected):
                    render_artifact.validate_planning(data)

    def test_phase_and_intra_phase_orders_are_unique(self) -> None:
        phase_data = valid_planning()
        phase_data["phases"][1]["order"] = 1
        with self.assertRaisesRegex(render_artifact.ConfigError, "phase dupliqué"):
            render_artifact.validate_planning(phase_data)

        segment_data = valid_planning()
        segment_data["segments"][1]["order"] = 1
        with self.assertRaisesRegex(render_artifact.ConfigError, "segment dupliqué"):
            render_artifact.validate_planning(segment_data)

    def test_dependency_cannot_be_in_a_future_phase(self) -> None:
        data = valid_planning()
        data["segments"][0]["dependencies"] = ["S3"]
        data["segments"][1]["dependencies"] = []
        data["segments"][2]["dependencies"] = []
        with self.assertRaisesRegex(render_artifact.ConfigError, "phase future"):
            render_artifact.validate_planning(data)

    def test_same_phase_dependency_must_have_lower_order(self) -> None:
        data = valid_planning()
        data["segments"][0]["dependencies"] = ["S2"]
        data["segments"][1]["dependencies"] = []
        with self.assertRaisesRegex(render_artifact.ConfigError, "ordre inférieur"):
            render_artifact.validate_planning(data)

    def test_cycles_are_rejected_before_order_checks(self) -> None:
        data = valid_planning()
        data["segments"][0]["dependencies"] = ["S2"]
        with self.assertRaisesRegex(render_artifact.ConfigError, "Cycle"):
            render_artifact.validate_planning(data)

    def test_open_question_segment_must_exist(self) -> None:
        data = valid_planning()
        data["open_questions"][0]["segment"] = "S99"
        with self.assertRaisesRegex(render_artifact.ConfigError, "Segment inconnu"):
            render_artifact.validate_planning(data)

    def test_open_question_severity_is_strict(self) -> None:
        data = valid_planning()
        data["open_questions"][0]["severity"] = "avant ouverture"
        with self.assertRaisesRegex(render_artifact.ConfigError, "avant-segment"):
            render_artifact.validate_planning(data)

    def test_open_question_ids_are_optional_safe_and_unique(self) -> None:
        optional = valid_planning()
        del optional["open_questions"][0]["id"]
        render_artifact.validate_planning(optional)

        duplicate = valid_planning()
        duplicate["open_questions"].append(
            {
                "id": "SupportOwner",
                "text": "Quel délai de réponse ?",
                "severity": "avant-segment",
            }
        )
        with self.assertRaisesRegex(render_artifact.ConfigError, "dupliqué"):
            render_artifact.validate_planning(duplicate)


class RenderingTests(unittest.TestCase):
    def write_json(self, directory: Path, name: str, data: object) -> Path:
        path = directory / name
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def test_good_questionnaire_and_planning_render(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            for kind, data in (
                ("questionnaire", valid_questionnaire()),
                ("planning", valid_planning()),
            ):
                with self.subTest(kind=kind):
                    source = self.write_json(directory, f"{kind}.json", data)
                    output = directory / f"{kind}.html"
                    render_artifact.render(kind, source, output)
                    rendered = output.read_text(encoding="utf-8")
                    self.assertNotIn("__PROJECT_DATA__", rendered)
                    self.assertIn(data["schema"], rendered)
                    self.assertTrue(rendered.startswith("<!doctype html>"))

    def test_bundled_v2_examples_validate_and_render(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            for kind, suffix in (
                ("questionnaire", ""),
                ("planning", ""),
                ("questionnaire", ".en"),
                ("planning", ".en"),
            ):
                with self.subTest(kind=kind, suffix=suffix):
                    source = SKILL_ROOT / "references" / f"{kind}-example{suffix}.json"
                    output = directory / f"{kind}{suffix}.html"
                    render_artifact.render(kind, source, output)
                    self.assertTrue(output.is_file())
                    self.assertNotIn(
                        "__PROJECT_DATA__", output.read_text(encoding="utf-8")
                    )

    def test_input_and_output_must_be_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            path = self.write_json(
                Path(raw_directory), "questionnaire.json", valid_questionnaire()
            )
            with self.assertRaisesRegex(render_artifact.ConfigError, "distincts"):
                render_artifact.render("questionnaire", path, path)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8"))["schema"],
                "project-workshop-questionnaire-v2",
            )

    def test_atomic_render_leaves_no_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            source = self.write_json(directory, "planning.json", valid_planning())
            output = directory / "planning.html"
            output.write_text("ancienne version", encoding="utf-8")
            render_artifact.render("planning", source, output)
            self.assertNotEqual(output.read_text(encoding="utf-8"), "ancienne version")
            self.assertEqual(list(directory.glob(".planning.html.*.tmp")), [])

    def test_planning_is_rendered_in_phase_and_segment_order(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            data = valid_planning()
            data["segments"] = list(reversed(data["segments"]))
            source = self.write_json(directory, "planning.json", data)
            output = directory / "planning.html"
            render_artifact.render("planning", source, output)
            rendered = output.read_text(encoding="utf-8")
            positions = [rendered.index(f'"id":"{segment_id}"') for segment_id in ("S1", "S2", "S3")]
            self.assertEqual(positions, sorted(positions))

    def test_schema_files_are_valid_json_and_name_v2_contracts(self) -> None:
        expected = {
            "questionnaire.schema.json": "project-workshop-questionnaire-v2",
            "planning.schema.json": "project-workshop-planning-v2",
        }
        for name, schema_name in expected.items():
            with self.subTest(name=name):
                schema = json.loads(
                    (SKILL_ROOT / "references" / name).read_text(encoding="utf-8")
                )
                self.assertEqual(schema["properties"]["schema"]["const"], schema_name)
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertEqual(schema["properties"]["locale"]["enum"], ["fr", "en"])
                self.assertEqual(schema["properties"]["locale"]["default"], "fr")

    def test_safe_json_neutralizes_script_end_tags(self) -> None:
        encoded = render_artifact.safe_json({"value": "</script><script>"})
        self.assertNotIn("<", encoded)
        self.assertIn("\\u003c/script>", encoded)


if __name__ == "__main__":
    unittest.main()
