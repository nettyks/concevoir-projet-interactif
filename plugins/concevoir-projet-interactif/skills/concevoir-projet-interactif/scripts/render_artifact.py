#!/usr/bin/env python3
"""Render a self-contained project questionnaire or planning board."""

from __future__ import annotations

import argparse
import copy
from html import escape
import json
import os
import re
import stat
import sys
import tempfile
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

QUESTIONNAIRE_SCHEMA = "project-workshop-questionnaire-v2"
PLANNING_SCHEMA = "project-workshop-planning-v2"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SAFE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
THEME_URL_RE = re.compile(
    r"url\s*\(|@import|(?:https?|file|data|javascript)\s*:", re.IGNORECASE
)

QUESTION_TYPES = {
    "open",
    "decision",
    "single_choice",
    "multi_choice",
    "scale",
    "ranking",
}
LOCALES = {"fr", "en"}
CHOICE_TONES = {"neutral", "positive", "warning", "negative"}
OPEN_QUESTION_SEVERITIES = {"bloquant", "avant-segment", "differable"}
DEFAULT_STATUSES = {
    "a-preciser",
    "pret",
    "en-cours",
    "verification",
    "termine",
}
THEME_KEYS = {
    "accent",
    "bg",
    "danger",
    "font",
    "focus",
    "line",
    "max",
    "maybe",
    "muted",
    "negative",
    "neutral",
    "no",
    "positive",
    "primary",
    "radius",
    "surface",
    "surface_2",
    "text",
    "warning",
    "yes",
}
DEFAULT_DECISION_CHOICES = {
    "fr": [
        {"id": "yes", "label": "Oui", "tone": "positive", "needs_clarification": False},
        {"id": "no", "label": "Non", "tone": "negative", "needs_clarification": False},
        {"id": "maybe", "label": "Peut-être", "tone": "warning", "needs_clarification": True},
    ],
    "en": [
        {"id": "yes", "label": "Yes", "tone": "positive", "needs_clarification": False},
        {"id": "no", "label": "No", "tone": "negative", "needs_clarification": False},
        {"id": "maybe", "label": "Maybe", "tone": "warning", "needs_clarification": True},
    ],
}


class ConfigError(ValueError):
    """Raised when an artifact configuration is inconsistent."""


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{label} doit être un objet JSON")
    return value


def reject_unknown_keys(
    obj: dict[str, Any], allowed: Iterable[str], label: str
) -> None:
    unknown = sorted(set(obj) - set(allowed))
    if unknown:
        raise ConfigError(
            f"Clé(s) inconnue(s) dans {label}: {', '.join(unknown)}"
        )


def require_text(obj: dict[str, Any], key: str, label: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{label}.{key} doit être un texte non vide")
    return value.strip()


def validate_optional_text(obj: dict[str, Any], key: str, label: str) -> None:
    if key in obj:
        require_text(obj, key, label)


def require_id(obj: dict[str, Any], key: str, label: str) -> str:
    raw_value = obj.get(key)
    value = require_text(obj, key, label)
    if raw_value != value:
        raise ConfigError(f"{label}.{key} ne doit pas commencer ou finir par un espace")
    if not SAFE_ID_RE.fullmatch(value):
        raise ConfigError(
            f"{label}.{key} doit respecter {SAFE_ID_RE.pattern}"
        )
    return value


def require_bool(obj: dict[str, Any], key: str, label: str) -> bool:
    value = obj.get(key)
    if not isinstance(value, bool):
        raise ConfigError(f"{label}.{key} doit être un booléen")
    return value


def require_integer(
    obj: dict[str, Any], key: str, label: str, minimum: int = 1
) -> int:
    value = obj.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ConfigError(
            f"{label}.{key} doit être un entier supérieur ou égal à {minimum}"
        )
    return value


def require_list(value: Any, label: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        raise ConfigError(f"{label} doit être une liste")
    if nonempty and not value:
        raise ConfigError(f"{label} doit être une liste non vide")
    return value


def require_object_list(
    value: Any, label: str, *, nonempty: bool = False
) -> list[dict[str, Any]]:
    values = require_list(value, label, nonempty=nonempty)
    result: list[dict[str, Any]] = []
    for index, item in enumerate(values):
        result.append(require_object(item, f"{label}[{index}]"))
    return result


def require_text_list(
    obj: dict[str, Any],
    key: str,
    label: str,
    *,
    nonempty: bool = False,
    unique: bool = False,
) -> list[str]:
    values = require_list(obj.get(key), f"{label}.{key}", nonempty=nonempty)
    result: list[str] = []
    for index, item in enumerate(values):
        if not isinstance(item, str) or not item.strip():
            raise ConfigError(
                f"{label}.{key}[{index}] doit être un texte non vide"
            )
        result.append(item.strip())
    if unique and len(result) != len(set(result)):
        raise ConfigError(f"{label}.{key} ne doit pas contenir de doublon")
    return result


def unique_ids(items: list[dict[str, Any]], label: str) -> set[str]:
    seen: set[str] = set()
    for index, item in enumerate(items):
        item_id = require_id(item, "id", f"{label}[{index}]")
        if item_id in seen:
            raise ConfigError(f"Identifiant dupliqué dans {label}: {item_id}")
        seen.add(item_id)
    return seen


def validate_project(data: dict[str, Any]) -> None:
    project = require_object(data.get("project"), "project")
    reject_unknown_keys(project, {"title", "slug", "subtitle"}, "project")
    require_text(project, "title", "project")
    slug = require_text(project, "slug", "project")
    if project.get("slug") != slug:
        raise ConfigError("project.slug ne doit pas commencer ou finir par un espace")
    if not SLUG_RE.fullmatch(slug):
        raise ConfigError("project.slug doit utiliser minuscules, chiffres et tirets")
    validate_optional_text(project, "subtitle", "project")


def validate_storage_key(data: dict[str, Any]) -> None:
    storage_key = require_text(data, "storage_key", "racine")
    if any(char.isspace() for char in storage_key):
        raise ConfigError("storage_key ne doit pas contenir d'espace")


def validate_locale(data: dict[str, Any]) -> None:
    if "locale" not in data:
        return
    locale = require_text(data, "locale", "racine")
    if locale not in LOCALES:
        raise ConfigError("locale doit valoir fr ou en")


def validate_theme(data: dict[str, Any]) -> None:
    if "theme" not in data:
        return
    theme = require_object(data["theme"], "theme")
    reject_unknown_keys(theme, THEME_KEYS, "theme")
    for key, value in theme.items():
        if not isinstance(value, str) or not value.strip():
            raise ConfigError(f"theme.{key} doit être un texte non vide")
        if THEME_URL_RE.search(value):
            raise ConfigError(f"theme.{key} ne doit contenir aucune URL")


def require_number(obj: dict[str, Any], key: str, label: str) -> float:
    value = obj.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{label}.{key} doit être un nombre")
    if value != value or value in {float("inf"), float("-inf")}:
        raise ConfigError(f"{label}.{key} doit être un nombre fini")
    return float(value)


def validate_scale(scale: dict[str, Any], label: str) -> None:
    allowed = {"min", "max", "step", "default", "min_label", "max_label"}
    reject_unknown_keys(scale, allowed, label)
    missing = sorted(allowed - set(scale))
    if missing:
        raise ConfigError(
            f"Clé(s) obligatoire(s) manquante(s) dans {label}: "
            + ", ".join(missing)
        )
    minimum = require_number(scale, "min", label)
    maximum = require_number(scale, "max", label)
    step = require_number(scale, "step", label)
    default = require_number(scale, "default", label)
    require_text(scale, "min_label", label)
    require_text(scale, "max_label", label)
    if maximum <= minimum:
        raise ConfigError(f"{label}.max doit être supérieur à {label}.min")
    if step <= 0:
        raise ConfigError(f"{label}.step doit être strictement positif")
    if not minimum <= default <= maximum:
        raise ConfigError(f"{label}.default doit être compris entre min et max")
    steps = (default - minimum) / step
    if abs(steps - round(steps)) > 1e-9:
        raise ConfigError(f"{label}.default doit respecter le pas défini par step")


def validate_choice(choice: dict[str, Any], label: str) -> None:
    reject_unknown_keys(
        choice, {"id", "label", "tone", "needs_clarification"}, label
    )
    require_id(choice, "id", label)
    require_text(choice, "label", label)
    tone = require_text(choice, "tone", label)
    if tone not in CHOICE_TONES:
        raise ConfigError(
            f"{label}.tone doit valoir neutral, positive, warning ou negative"
        )
    require_bool(choice, "needs_clarification", label)


def validate_question(question: dict[str, Any], label: str) -> None:
    reject_unknown_keys(
        question,
        {
            "id",
            "type",
            "title",
            "description",
            "choices",
            "note_placeholder",
            "answer_placeholder",
            "allow_note",
            "scale",
        },
        label,
    )
    require_id(question, "id", label)
    require_text(question, "title", label)
    validate_optional_text(question, "description", label)
    validate_optional_text(question, "note_placeholder", label)
    validate_optional_text(question, "answer_placeholder", label)
    if "allow_note" in question:
        require_bool(question, "allow_note", label)
    question_type = require_text(question, "type", label)
    if question_type not in QUESTION_TYPES:
        raise ConfigError(
            f"{label}.type doit valoir {', '.join(sorted(QUESTION_TYPES))}"
        )

    if question_type == "scale":
        if "choices" in question:
            raise ConfigError(f"{label}.choices est interdit pour une question scale")
        scale = require_object(question.get("scale"), f"{label}.scale")
        validate_scale(scale, f"{label}.scale")
        return

    if "scale" in question:
        raise ConfigError(f"{label}.scale est réservé aux questions de type scale")

    if question_type == "open":
        if "choices" in question:
            raise ConfigError(f"{label}.choices est interdit pour une question open")
        return

    if question_type == "decision" and "choices" not in question:
        return

    choices = require_object_list(
        question.get("choices"), f"{label}.choices", nonempty=True
    )
    if len(choices) < 2:
        raise ConfigError(f"{label}.choices doit contenir au moins deux choix")
    if question_type == "decision" and len(choices) > 3:
        raise ConfigError(
            f"{label}.choices doit contenir deux ou trois choix pour une décision"
        )
    unique_ids(choices, f"{label}.choices")
    for index, choice in enumerate(choices):
        validate_choice(choice, f"{label}.choices[{index}]")


def validate_questionnaire(data: dict[str, Any]) -> None:
    reject_unknown_keys(
        data,
        {
            "schema",
            "locale",
            "project",
            "round_id",
            "round",
            "storage_key",
            "intro_title",
            "intro",
            "theme",
            "sections",
        },
        "racine",
    )
    schema = require_text(data, "schema", "racine")
    if schema != QUESTIONNAIRE_SCHEMA:
        raise ConfigError(f"schema doit valoir {QUESTIONNAIRE_SCHEMA}")
    validate_project(data)
    validate_locale(data)
    require_id(data, "round_id", "racine")
    require_text(data, "round", "racine")
    validate_storage_key(data)
    validate_optional_text(data, "intro_title", "racine")
    validate_optional_text(data, "intro", "racine")
    validate_theme(data)

    sections = require_object_list(
        data.get("sections"), "sections", nonempty=True
    )
    unique_ids(sections, "sections")
    questions: list[dict[str, Any]] = []
    for section_index, section in enumerate(sections):
        section_label = f"sections[{section_index}]"
        reject_unknown_keys(
            section, {"id", "title", "description", "questions"}, section_label
        )
        require_text(section, "title", section_label)
        validate_optional_text(section, "description", section_label)
        section_questions = require_object_list(
            section.get("questions"),
            f"{section_label}.questions",
            nonempty=True,
        )
        for question_index, question in enumerate(section_questions):
            validate_question(
                question, f"{section_label}.questions[{question_index}]"
            )
        questions.extend(section_questions)
    unique_ids(questions, "questions")


def detect_cycles(segments: list[dict[str, Any]], ids: set[str]) -> None:
    dependencies_by_id: dict[str, list[str]] = {}
    dependents: dict[str, list[str]] = defaultdict(list)
    remaining_dependencies: dict[str, int] = {}

    for segment in segments:
        segment_id = segment["id"]
        dependencies = segment["dependencies"]
        unknown = set(dependencies) - ids
        if unknown:
            raise ConfigError(
                f"Dépendances inconnues pour {segment_id}: "
                + ", ".join(sorted(unknown))
            )
        if segment_id in dependencies:
            raise ConfigError(f"{segment_id} ne peut pas dépendre de lui-même")
        dependencies_by_id[segment_id] = dependencies
        remaining_dependencies[segment_id] = len(dependencies)
        for dependency in dependencies:
            dependents[dependency].append(segment_id)

    ready = deque(
        sorted(
            segment_id
            for segment_id, count in remaining_dependencies.items()
            if count == 0
        )
    )
    visited = 0
    while ready:
        node = ready.popleft()
        visited += 1
        for dependent in sorted(dependents[node]):
            remaining_dependencies[dependent] -= 1
            if remaining_dependencies[dependent] == 0:
                ready.append(dependent)

    if visited != len(dependencies_by_id):
        cyclic = sorted(
            segment_id
            for segment_id, count in remaining_dependencies.items()
            if count > 0
        )
        raise ConfigError("Cycle de dépendances détecté: " + ", ".join(cyclic))


def validate_optional_metric(
    segment: dict[str, Any], key: str, label: str
) -> None:
    if key not in segment:
        return
    value = segment[key]
    if isinstance(value, bool):
        raise ConfigError(f"{label}.{key} doit être un texte ou un nombre positif")
    if isinstance(value, str):
        if value.strip():
            return
    elif isinstance(value, (int, float)):
        if value == value and value not in {float("inf"), float("-inf")} and value >= 0:
            return
    raise ConfigError(f"{label}.{key} doit être un texte ou un nombre positif")


def validate_planning(data: dict[str, Any]) -> None:
    reject_unknown_keys(
        data,
        {
            "schema",
            "locale",
            "project",
            "storage_key",
            "view",
            "theme",
            "phases",
            "columns",
            "open_questions",
            "segments",
        },
        "racine",
    )
    schema = require_text(data, "schema", "racine")
    if schema != PLANNING_SCHEMA:
        raise ConfigError(f"schema doit valoir {PLANNING_SCHEMA}")
    validate_project(data)
    validate_locale(data)
    validate_storage_key(data)
    validate_theme(data)
    view = require_text(data, "view", "racine")
    if view not in {"kanban", "roadmap"}:
        raise ConfigError("view doit valoir kanban ou roadmap")

    phases = require_object_list(data.get("phases"), "phases", nonempty=True)
    phase_ids = unique_ids(phases, "phases")
    phase_orders: dict[str, int] = {}
    used_phase_orders: set[int] = set()
    for index, phase in enumerate(phases):
        label = f"phases[{index}]"
        reject_unknown_keys(phase, {"id", "title", "order", "milestone"}, label)
        phase_id = phase["id"]
        require_text(phase, "title", label)
        order = require_integer(phase, "order", label)
        if order in used_phase_orders:
            raise ConfigError(f"Ordre de phase dupliqué: {order}")
        used_phase_orders.add(order)
        phase_orders[phase_id] = order
        validate_optional_text(phase, "milestone", label)

    allowed_statuses = set(DEFAULT_STATUSES)
    if "columns" in data:
        columns = require_object_list(data["columns"], "columns", nonempty=True)
        allowed_statuses = unique_ids(columns, "columns")
        for index, column in enumerate(columns):
            label = f"columns[{index}]"
            reject_unknown_keys(column, {"id", "title"}, label)
            require_text(column, "title", label)

    open_questions = require_object_list(
        data.get("open_questions"), "open_questions"
    )
    open_question_ids: set[str] = set()
    for index, question in enumerate(open_questions):
        label = f"open_questions[{index}]"
        reject_unknown_keys(question, {"id", "text", "severity", "segment"}, label)
        if "id" in question:
            question_id = require_id(question, "id", label)
            if question_id in open_question_ids:
                raise ConfigError(
                    f"Identifiant dupliqué dans open_questions: {question_id}"
                )
            open_question_ids.add(question_id)
        require_text(question, "text", label)
        severity = require_text(question, "severity", label)
        if severity not in OPEN_QUESTION_SEVERITIES:
            raise ConfigError(
                f"{label}.severity doit valoir bloquant, avant-segment ou differable"
            )
        if "segment" in question:
            require_id(question, "segment", label)

    segments = require_object_list(data.get("segments"), "segments", nonempty=True)
    segment_ids = unique_ids(segments, "segments")
    segments_by_id: dict[str, dict[str, Any]] = {}
    orders_by_phase: dict[str, set[int]] = defaultdict(set)
    required_segment_keys = {
        "id",
        "title",
        "objective",
        "phase",
        "status",
        "order",
        "dependencies",
        "decision_refs",
        "deliverables",
        "acceptance",
        "prerequisites",
        "risks",
        "questions",
    }
    optional_segment_keys = {"summary", "owner", "effort", "priority"}

    for index, segment in enumerate(segments):
        label = f"segments[{index}]"
        reject_unknown_keys(
            segment, required_segment_keys | optional_segment_keys, label
        )
        missing = sorted(required_segment_keys - set(segment))
        if missing:
            raise ConfigError(
                f"Clé(s) obligatoire(s) manquante(s) dans {label}: "
                + ", ".join(missing)
            )
        segment_id = segment["id"]
        require_text(segment, "title", label)
        require_text(segment, "objective", label)
        validate_optional_text(segment, "summary", label)
        phase_id = require_id(segment, "phase", label)
        if phase_id not in phase_ids:
            raise ConfigError(f"Phase inconnue pour {segment_id}: {phase_id}")
        status = require_id(segment, "status", label)
        if status not in allowed_statuses:
            raise ConfigError(f"Statut inconnu pour {segment_id}: {status}")
        order = require_integer(segment, "order", label)
        if order in orders_by_phase[phase_id]:
            raise ConfigError(
                f"Ordre de segment dupliqué dans la phase {phase_id}: {order}"
            )
        orders_by_phase[phase_id].add(order)

        segment["dependencies"] = require_text_list(
            segment, "dependencies", label, unique=True
        )
        segment["decision_refs"] = require_text_list(
            segment, "decision_refs", label, nonempty=True, unique=True
        )
        for reference in segment["decision_refs"]:
            if not SAFE_ID_RE.fullmatch(reference):
                raise ConfigError(
                    f"{label}.decision_refs contient un identifiant invalide: {reference}"
                )
        require_text_list(segment, "deliverables", label, nonempty=True)
        require_text_list(segment, "acceptance", label, nonempty=True)
        require_text_list(segment, "prerequisites", label)
        require_text_list(segment, "risks", label)
        require_text_list(segment, "questions", label)
        validate_optional_text(segment, "owner", label)
        validate_optional_metric(segment, "effort", label)
        validate_optional_metric(segment, "priority", label)
        segments_by_id[segment_id] = segment

    detect_cycles(segments, segment_ids)

    for segment in segments:
        segment_id = segment["id"]
        segment_phase = segment["phase"]
        segment_phase_order = phase_orders[segment_phase]
        segment_order = segment["order"]
        for dependency_id in segment["dependencies"]:
            dependency = segments_by_id[dependency_id]
            dependency_phase = dependency["phase"]
            dependency_phase_order = phase_orders[dependency_phase]
            if dependency_phase_order > segment_phase_order:
                raise ConfigError(
                    f"{segment_id} dépend de {dependency_id}, placé dans une phase future"
                )
            if (
                dependency_phase_order == segment_phase_order
                and dependency["order"] >= segment_order
            ):
                raise ConfigError(
                    f"{segment_id} dépend de {dependency_id}, qui doit avoir un ordre "
                    f"inférieur dans la phase {segment_phase}"
                )

    for index, question in enumerate(open_questions):
        segment_id = question.get("segment")
        if segment_id is not None and segment_id not in segment_ids:
            raise ConfigError(
                f"Segment inconnu dans open_questions[{index}]: {segment_id}"
            )


def safe_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace(
        "<", "\\u003c"
    )


def paths_refer_to_same_file(source: Path, output: Path) -> bool:
    try:
        if source.resolve() == output.resolve():
            return True
    except OSError:
        pass
    try:
        return source.exists() and output.exists() and os.path.samefile(source, output)
    except OSError:
        return False


def atomic_write_text(output: Path, content: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output_mode = 0o644
    try:
        if output.exists():
            output_mode = stat.S_IMODE(output.stat().st_mode)
    except OSError:
        pass

    descriptor, temporary_name = tempfile.mkstemp(
        dir=str(output.parent), prefix=f".{output.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_name, output_mode)
        os.replace(temporary_name, output)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def normalized_for_render(kind: str, data: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(data)
    if kind == "questionnaire":
        locale = normalized.get("locale", "fr")
        for section in normalized["sections"]:
            for question in section["questions"]:
                if question["type"] == "decision" and "choices" not in question:
                    question["choices"] = copy.deepcopy(DEFAULT_DECISION_CHOICES[locale])
        return normalized

    phase_orders = {phase["id"]: phase["order"] for phase in normalized["phases"]}
    normalized["phases"].sort(key=lambda phase: (phase["order"], phase["id"]))
    for segment in normalized["segments"]:
        segment.setdefault("summary", segment["objective"])
    normalized["segments"].sort(
        key=lambda segment: (
            phase_orders[segment["phase"]],
            segment["order"],
            segment["id"],
        )
    )
    return normalized


def reading_html(kind: str, data: dict[str, Any]) -> str:
    """Render a static reading sheet; replies and changes belong in the chat."""
    en = data.get("locale", "fr") == "en"
    def tr(fr: str, english: str) -> str:
        return english if en else fr
    def esc(value: Any) -> str:
        return escape(str(value), quote=True)
    def paragraph(value: Any, cls: str = "") -> str:
        return f'<p class="{cls}">{esc(value)}</p>' if value else ""
    def listing(values: list[str]) -> str:
        return '<ul>' + ''.join(f'<li>{esc(value)}</li>' for value in values) + '</ul>'
    title = data["project"]["title"]
    content = '<header>' + paragraph(tr('Fiche de lecture', 'Reading sheet'), 'eyebrow')
    content += f'<h1>{esc(title)}</h1>' + paragraph(data["project"].get("subtitle"))
    content += paragraph(tr('Lis les propositions ici, puis réponds directement dans le chat. La fiche sera mise à jour à partir de tes réponses.',
                            'Read the proposals here, then reply directly in the chat. The sheet will be updated from your answers.')) + '</header>'
    if kind == "questionnaire":
        content += paragraph(data.get("round", data["round_id"]), 'eyebrow')
        content += f'<h2>{esc(data.get("intro_title", ""))}</h2>' + paragraph(data.get("intro"))
        content += '<nav>' + ''.join(f'<a href="#section-{esc(s["id"])}">{esc(s["title"])}</a>' for s in data["sections"]) + '</nav>'
        types = {"open": tr('Réponse libre', 'Open answer'), "decision": tr('Proposition à discuter', 'Proposal to discuss'),
                 "single_choice": tr('Une option à choisir', 'Choose one option'), "multi_choice": tr('Plusieurs options possibles', 'Multiple options allowed'),
                 "scale": tr('Échelle à discuter', 'Rating to discuss'), "ranking": tr('Éléments à classer', 'Items to rank')}
        for section in data["sections"]:
            content += f'<section id="section-{esc(section["id"])}"><h2>{esc(section["title"])}</h2>' + paragraph(section.get("description"))
            for q in section["questions"]:
                content += f'<article id="question-{esc(q["id"])}">' + paragraph(q["id"], 'id')
                content += f'<h3>{esc(q["title"])}</h3>' + paragraph(q.get("description")) + paragraph(types[q["type"]], 'type')
                if q.get("choices"):
                    content += listing([c["label"] + (tr(' — à préciser', ' — add detail') if c["needs_clarification"] else '') for c in q["choices"]])
                if q["type"] == "scale":
                    s = q["scale"]
                    content += paragraph(f'{s["min"]} — {s["min_label"]} / {s["max"]} — {s["max_label"]}')
                    content += paragraph(tr('Pas : ', 'Step: ') + str(s["step"]), 'hint')
                content += paragraph(q.get("answer_placeholder"), 'hint') + paragraph(q.get("note_placeholder"), 'hint')
                content += '</article>'
            content += '</section>'
    else:
        phases = sorted(data["phases"], key=lambda phase: phase["order"])
        phase_titles = {p["id"]: p["title"] for p in phases}
        defaults = list(zip(['a-preciser', 'pret', 'en-cours', 'verification', 'termine'],
                            ['To clarify', 'Ready', 'In progress', 'Verification', 'Done'] if en else ['À préciser', 'Prêt', 'En cours', 'Vérification', 'Terminé']))
        columns = data.get("columns", [{"id": key, "title": value} for key, value in defaults])
        statuses = {column["id"]: column["title"] for column in columns}
        segments = sorted(data["segments"], key=lambda s: (next(p["order"] for p in phases if p["id"] == s["phase"]), s["order"]))
        severity = {'bloquant': tr('Bloquant', 'Blocking'), 'avant-segment': tr('Avant le segment', 'Before the segment'), 'differable': tr('Différable', 'Deferrable')}
        content += '<a href="../questionnaire-actif.html">' + tr('Lire les propositions et questions', 'Read proposals and questions') + '</a>'
        content += '<h2>' + tr('Points ouverts', 'Open questions') + '</h2>'
        content += listing([' · '.join(filter(None, [q.get('id'), q['text'], severity[q['severity']], q.get('segment')])) for q in data['open_questions']])
        def card(s: dict[str, Any], view: str) -> str:
            result = f'<article id="{view}-{esc(s["id"])}">' + paragraph(s['id'], 'id') + f'<h3>{esc(s["title"])}</h3>'
            result += paragraph(s.get('summary')) + paragraph(s['objective']) + '<dl>'
            for label, value in [(tr('Phase', 'Phase'), phase_titles[s['phase']]), (tr('État', 'Status'), statuses[s['status']]),
                                 (tr('Ordre', 'Order'), s['order']), (tr('Responsable', 'Owner'), s.get('owner')),
                                 (tr('Effort', 'Effort'), s.get('effort')), (tr('Priorité', 'Priority'), s.get('priority'))]:
                if value is not None:
                    result += f'<dt>{esc(label)}</dt><dd>{esc(value)}</dd>'
            result += '</dl><details><summary>' + tr('Détails du segment', 'Segment details') + '</summary>'
            for key, label in [('dependencies', tr('Dépendances', 'Dependencies')), ('decision_refs', tr('Décisions', 'Decisions')),
                               ('deliverables', tr('Livrables', 'Deliverables')), ('acceptance', tr('Critères de réussite', 'Acceptance criteria')),
                               ('prerequisites', tr('Prérequis', 'Prerequisites')), ('risks', tr('Risques', 'Risks')), ('questions', tr('Questions', 'Questions'))]:
                result += f'<h4>{esc(label)}</h4>' + (listing(s[key]) if s[key] else paragraph(tr('Aucun', 'None')))
            return result + '</details></article>'
        for view, groups in [('roadmap', phases), ('kanban', columns)]:
            opened = ' open' if data['view'] == view else ''
            content += f'<details{opened}><summary>{view.capitalize()}</summary><div class="columns">'
            for group in groups:
                content += f'<section><h2>{esc(group["title"])}</h2>' + paragraph(group.get('milestone'))
                content += ''.join(card(s, view) for s in segments if s['phase' if view == 'roadmap' else 'status'] == group['id']) + '</section>'
            content += '</div></details>'
    theme = ';'.join('--' + key.replace('_', '-') + ':' + value for key, value in data.get('theme', {}).items()
                     if re.fullmatch(r'#[0-9a-fA-F]{3,8}|[0-9]+(?:\.[0-9]+)?(?:px|rem)', value))
    replacements = {'LOCALE': 'en' if en else 'fr', 'TITLE': esc(title), 'THEME': esc(theme), 'CONTENT': content}
    template = (ASSETS / 'reading-template.html').read_text(encoding='utf-8')
    return re.sub(r'__READING_(LOCALE|TITLE|THEME|CONTENT)__', lambda match: replacements[match[1]], template)


def render(kind: str, source: Path, output: Path, *, inline: bool = False, read_only: bool = False) -> None:
    if kind not in {"questionnaire", "planning"}:
        raise ConfigError("kind doit valoir questionnaire ou planning")
    if inline and kind != "questionnaire":
        raise ConfigError("--inline est réservé aux questionnaires")
    if inline and read_only:
        raise ConfigError("--inline et --read-only sont incompatibles")
    if paths_refer_to_same_file(source, output):
        raise ConfigError("Le fichier d'entrée et le fichier de sortie doivent être distincts")

    with source.open("r", encoding="utf-8") as handle:
        data = require_object(json.load(handle), "racine")
    if kind == "questionnaire":
        validate_questionnaire(data)
        template_path = ASSETS / (
            "questionnaire-inline.html" if inline else "questionnaire-template.html"
        )
    else:
        validate_planning(data)
        template_path = ASSETS / "planning-template.html"

    if read_only:
        atomic_write_text(output, reading_html(kind, normalized_for_render(kind, data)))
        print(f"Créé: {output}")
        return

    template = template_path.read_text(encoding="utf-8")
    marker = "__PROJECT_DATA__"
    if template.count(marker) != 1:
        raise ConfigError(
            f"Le modèle {template_path.name} doit contenir exactement un marqueur {marker}"
        )
    rendered_data = normalized_for_render(kind, data)
    if inline:
        # Insert maintained code before user data, so data cannot act as a marker.
        template = template.replace(
            "__CONVERSATION_RUNTIME__",
            (ASSETS / "questionnaire-conversation.js").read_text(encoding="utf-8"),
        )
        import hashlib
        root_id = "questionnaire-" + hashlib.sha256(
            (data["project"]["slug"] + ":" + data["round_id"] + ":" + data["storage_key"]).encode()
        ).hexdigest()[:16]
        template = template.replace("__ROOT_ID__", root_id)
    rendered = template.replace(marker, safe_json(rendered_data))
    if inline and len(rendered.encode("utf-8")) >= 1_000_000:
        raise ConfigError("Questionnaire trop grand pour la conversation ; diviser le tour")
    atomic_write_text(output, rendered)
    print(f"Créé: {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("questionnaire", "planning"))
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--inline", action="store_true", help="questionnaire dans la conversation avec envoi des réponses")
    modes.add_argument("--read-only", action="store_true", help="fiche de lecture ; réponses et modifications dans le chat")
    args = parser.parse_args()
    try:
        render(args.kind, args.input, args.output, inline=args.inline, read_only=args.read_only)
    except (ConfigError, OSError, json.JSONDecodeError) as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
