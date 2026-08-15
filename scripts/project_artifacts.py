#!/usr/bin/env python3
"""Initialize and archive durable artifacts for a digital project workshop."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SAFE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DECISION_KINDS = {"fact", "decision", "constraint", "hypothesis", "open_question"}
DECISION_STATUSES = {"proposed", "accepted", "rejected", "deferred", "superseded"}
CONFIDENCE_VALUES = {"verified", "high", "medium", "low", "unknown"}
PRIORITY_VALUES = {None, "indispensable", "important", "differable"}


class ArtifactError(ValueError):
    """Raised when project artifacts cannot be handled safely."""


def reject_unknown_keys(obj: dict[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(obj) - allowed)
    if unknown:
        raise ArtifactError(f"Clé(s) inconnue(s) dans {label}: {', '.join(unknown)}")


def require_text(obj: dict[str, Any], key: str, label: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ArtifactError(f"{label}.{key} doit être un texte non vide")
    return value.strip()


def safe_project_dir(raw: Path) -> Path:
    project_dir = raw.expanduser().resolve()
    forbidden = {Path("/"), Path.home().resolve()}
    if project_dir in forbidden:
        raise ArtifactError("--project-dir doit viser un projet dédié, pas la racine ou le dossier personnel")
    return project_dir


def render_template(name: str, title: str, slug: str) -> str:
    source = (ASSETS / name).read_text(encoding="utf-8")
    return (
        source.replace("{{PROJECT_TITLE}}", title)
        .replace("{{PROJECT_SLUG}}", slug)
        .replace("{{CREATED_DATE}}", date.today().isoformat())
    )


def write_if_missing(path: Path, content: str) -> bool:
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(content)
    except FileExistsError:
        return False
    return True


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def initialize(project_dir: Path, title: str, slug: str) -> None:
    if not title.strip():
        raise ArtifactError("--title doit être un texte non vide")
    if not SLUG_RE.fullmatch(slug):
        raise ArtifactError("--slug doit utiliser minuscules, chiffres et tirets")

    project_dir.mkdir(parents=True, exist_ok=True)
    conception = project_dir / "conception"
    (conception / "tours").mkdir(parents=True, exist_ok=True)
    (conception / "planning").mkdir(parents=True, exist_ok=True)

    templates = {
        "journal.md": "journal-template.md",
        "decisions.json": "decisions-template.json",
        "sources.md": "sources-template.md",
        "specification.md": "specification-template.md",
    }
    for output_name, template_name in templates.items():
        output = conception / output_name
        created = write_if_missing(output, render_template(template_name, title.strip(), slug))
        print(("Créé: " if created else "Conservé: ") + str(output))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_answer_export(path: Path) -> None:
    if path.suffix.lower() != ".json":
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactError(f"Export JSON illisible {path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema") != "project-workshop-answers-v2":
        raise ArtifactError(f"{path} n'est pas un export de réponses V2")


def append_journal(journal: Path, round_id: str, archived_at: str) -> None:
    if not journal.exists():
        raise ArtifactError(f"Journal absent: {journal}; lancer d'abord la commande init")
    content = journal.read_text(encoding="utf-8")
    entry = f"- {archived_at[:10]} — Tour {round_id} archivé avec empreintes SHA-256."
    if entry in content:
        return
    separator = "" if content.endswith("\n") else "\n"
    atomic_write(journal, content + separator + entry + "\n")


def archive_round(
    project_dir: Path,
    round_id: str,
    questionnaire: Path,
    answers: list[Path],
) -> None:
    if not SAFE_ID_RE.fullmatch(round_id):
        raise ArtifactError("--round-id doit commencer par une lettre et contenir seulement lettres, chiffres, _ ou -")
    questionnaire = questionnaire.expanduser().resolve()
    if not questionnaire.is_file():
        raise ArtifactError(f"Questionnaire introuvable: {questionnaire}")
    if questionnaire.suffix.lower() not in {".html", ".htm"}:
        raise ArtifactError("--questionnaire doit être un fichier HTML")

    answer_paths = [path.expanduser().resolve() for path in answers]
    if not answer_paths:
        raise ArtifactError("Fournir au moins un --answers")
    for answer in answer_paths:
        if not answer.is_file():
            raise ArtifactError(f"Export de réponses introuvable: {answer}")
        validate_answer_export(answer)

    conception = project_dir / "conception"
    tours = conception / "tours"
    journal = conception / "journal.md"
    if not tours.is_dir():
        raise ArtifactError(f"Dossier de conception absent: {tours}; lancer d'abord la commande init")
    target = tours / round_id
    if target.exists():
        raise ArtifactError(f"Le tour {round_id} est déjà archivé: {target}")

    temporary = Path(tempfile.mkdtemp(prefix=f".{round_id}-", dir=tours))
    archived_at = datetime.now().astimezone().isoformat(timespec="seconds")
    manifest_files: list[dict[str, str]] = []
    try:
        questionnaire_target = temporary / "questionnaire.html"
        shutil.copy2(questionnaire, questionnaire_target)
        manifest_files.append({"name": questionnaire_target.name, "sha256": sha256(questionnaire_target)})

        for index, answer in enumerate(answer_paths, start=1):
            suffix = answer.suffix.lower() or ".txt"
            answer_target = temporary / f"reponses-{index:02d}{suffix}"
            shutil.copy2(answer, answer_target)
            manifest_files.append({"name": answer_target.name, "sha256": sha256(answer_target)})

        manifest = {
            "schema": "project-workshop-round-archive-v2",
            "round_id": round_id,
            "archived_at": archived_at,
            "files": manifest_files,
        }
        (temporary / "archive.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporary.rename(target)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise

    append_journal(journal, round_id, archived_at)
    print(f"Archivé: {target}")


def require_string_list(obj: dict[str, Any], key: str, label: str) -> list[str]:
    value = obj.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ArtifactError(f"{label}.{key} doit être une liste de textes non vides")
    return value


def validate_decisions(path: Path) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactError(f"Registre illisible: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") != "project-workshop-decisions-v2":
        raise ArtifactError("Le registre doit utiliser schema=project-workshop-decisions-v2")
    reject_unknown_keys(data, {"schema", "project", "updated_at", "decisions"}, "racine")
    project = data.get("project")
    if not isinstance(project, dict):
        raise ArtifactError("project doit être un objet")
    reject_unknown_keys(project, {"title", "slug"}, "project")
    require_text(project, "title", "project")
    slug = require_text(project, "slug", "project")
    if not SLUG_RE.fullmatch(slug):
        raise ArtifactError("project.slug est invalide")
    updated_at = data.get("updated_at")
    if updated_at is not None and (not isinstance(updated_at, str) or not DATE_RE.fullmatch(updated_at)):
        raise ArtifactError("updated_at doit être null ou une date YYYY-MM-DD")
    decisions = data.get("decisions")
    if not isinstance(decisions, list):
        raise ArtifactError("decisions doit être une liste")

    ids: set[str] = set()
    supersedes_by_id: dict[str, list[str]] = {}
    required_decision_keys = {
        "id", "kind", "status", "title", "rationale", "source_round",
        "source_questions", "evidence", "confidence", "owner", "priority",
        "supersedes", "created_at", "updated_at",
    }
    for index, decision in enumerate(decisions):
        label = f"decisions[{index}]"
        if not isinstance(decision, dict):
            raise ArtifactError(f"{label} doit être un objet")
        reject_unknown_keys(decision, required_decision_keys, label)
        missing = sorted(required_decision_keys - set(decision))
        if missing:
            raise ArtifactError(
                f"Clé(s) obligatoire(s) manquante(s) dans {label}: {', '.join(missing)}"
            )
        decision_id = require_text(decision, "id", label)
        if not SAFE_ID_RE.fullmatch(decision_id) or decision_id in {"__proto__", "prototype", "constructor"}:
            raise ArtifactError(f"{label}.id est invalide")
        if decision_id in ids:
            raise ArtifactError(f"Identifiant de décision dupliqué: {decision_id}")
        ids.add(decision_id)
        if decision.get("kind") not in DECISION_KINDS:
            raise ArtifactError(f"{label}.kind est invalide")
        if decision.get("status") not in DECISION_STATUSES:
            raise ArtifactError(f"{label}.status est invalide")
        require_text(decision, "title", label)
        if not isinstance(decision.get("rationale"), str):
            raise ArtifactError(f"{label}.rationale doit être un texte")
        source_round = decision.get("source_round")
        if source_round is not None and (not isinstance(source_round, str) or not SAFE_ID_RE.fullmatch(source_round)):
            raise ArtifactError(f"{label}.source_round est invalide")
        source_questions = require_string_list(decision, "source_questions", label)
        for question_id in source_questions:
            if not SAFE_ID_RE.fullmatch(question_id):
                raise ArtifactError(f"{label}.source_questions contient un identifiant invalide: {question_id}")
        evidence = require_string_list(decision, "evidence", label)
        if decision.get("confidence") not in CONFIDENCE_VALUES:
            raise ArtifactError(f"{label}.confidence est invalide")
        if decision.get("confidence") == "verified" and not evidence:
            raise ArtifactError(f"{label}.evidence doit contenir une preuve pour confidence=verified")
        owner = decision.get("owner")
        if owner is not None and not isinstance(owner, str):
            raise ArtifactError(f"{label}.owner doit être null ou un texte")
        if decision.get("priority") not in PRIORITY_VALUES:
            raise ArtifactError(f"{label}.priority est invalide")
        supersedes = require_string_list(decision, "supersedes", label)
        supersedes_by_id[decision_id] = supersedes
        for date_key in ("created_at", "updated_at"):
            value = decision.get(date_key)
            if not isinstance(value, str) or not DATE_RE.fullmatch(value):
                raise ArtifactError(f"{label}.{date_key} doit être une date YYYY-MM-DD")

    for decision_id, replaced in supersedes_by_id.items():
        unknown = set(replaced) - ids
        if unknown:
            raise ArtifactError(f"{decision_id} remplace des décisions inconnues: {', '.join(sorted(unknown))}")
        if decision_id in replaced:
            raise ArtifactError(f"{decision_id} ne peut pas se remplacer elle-même")
    print(f"Registre valide: {path} ({len(decisions)} décision(s))")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="initialiser conception/ sans écraser l'existant")
    init_parser.add_argument("--project-dir", required=True, type=Path)
    init_parser.add_argument("--title", required=True)
    init_parser.add_argument("--slug", required=True)

    archive_parser = subparsers.add_parser("archive", help="archiver un tour terminé")
    archive_parser.add_argument("--project-dir", required=True, type=Path)
    archive_parser.add_argument("--round-id", required=True)
    archive_parser.add_argument("--questionnaire", required=True, type=Path)
    archive_parser.add_argument("--answers", required=True, type=Path, action="append")

    validate_parser = subparsers.add_parser("validate-decisions", help="valider un registre de décisions V2")
    validate_parser.add_argument("--input", required=True, type=Path)

    args = parser.parse_args()
    try:
        if args.command == "init":
            initialize(safe_project_dir(args.project_dir), args.title, args.slug)
        elif args.command == "archive":
            archive_round(
                safe_project_dir(args.project_dir),
                args.round_id,
                args.questionnaire,
                args.answers,
            )
        else:
            validate_decisions(args.input.expanduser().resolve())
    except (ArtifactError, OSError) as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
