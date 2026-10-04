# Concevoir un projet numérique interactif

[![Tests](https://github.com/nettyks/concevoir-projet-interactif/actions/workflows/tests.yml/badge.svg)](https://github.com/nettyks/concevoir-projet-interactif/actions/workflows/tests.yml)

[Français](#francais) · [English](#english)

Un plugin Codex bilingue pour transformer une idée numérique en décisions traçables, spécification exploitable et plan de réalisation interactif.

A bilingual Codex plugin that turns a digital idea into traceable decisions, an actionable specification and an interactive delivery plan.

---

<a id="francais"></a>

## Français

### Ce que fait le plugin

Le plugin accompagne progressivement la conception de sites, applications, jeux, services en ligne, outils internes, automatisations, produits connectés et projets IA/data. Il s’adapte à une idée vague comme à un brief déjà précis et ne pose que les questions qui peuvent réellement changer le produit.

Il produit :

- des questionnaires Visualize dans la conversation, avec choix à cocher et champs de précision ;
- des réponses libres dans le chat également conservées par l’agent, et des fiches de lecture complémentaires si utiles ;
- un registre de décisions traçable avec hypothèses et décisions différées ;
- une spécification consolidée reliée aux décisions ;
- un plan lisible en Kanban et roadmap, mis à jour à partir des échanges ;
- un bouton dans le plan pour revenir directement aux questions ;
- des archives vérifiables des réponses brutes et des décisions.

Le fonctionnement par défaut : répondre au questionnaire Visualize directement dans la conversation,
avec des choix à cocher et un champ de précision, puis laisser l’agent consolider les décisions.
Les réponses libres restent acceptées. Si Visualize est indisponible, l’agent utilise les questions
natives visibles ou le texte du chat. Les fiches `--read-only` complètent la lecture et le planning ;
elles n’ont ni champ de réponse ni bouton d’envoi et fonctionnent sans JavaScript.

### Aperçu

Les captures suivantes illustrent les fiches autonomes ; le questionnaire par défaut s’affiche désormais dans la conversation via Visualize.

#### Questionnaire interactif

![Questionnaire interactif de cadrage](plugins/concevoir-projet-interactif/assets/screenshots/questionnaire.png)

#### Roadmap

![Roadmap horizontale du projet](plugins/concevoir-projet-interactif/assets/screenshots/planning-roadmap.png)

#### Kanban pilotable

![Kanban interactif du projet](plugins/concevoir-projet-interactif/assets/screenshots/planning-kanban.png)

### Installation depuis GitHub

Ajouter le dépôt comme marketplace Git puis installer le plugin :

~~~bash
codex plugin marketplace add nettyks/concevoir-projet-interactif --ref main
codex plugin add concevoir-projet-interactif@nettyks
~~~

Ouvrir ensuite une nouvelle tâche Codex pour charger le skill du plugin.

### Utilisation

~~~text
Utilise $concevoir-projet-interactif pour m’aider à cadrer ce projet numérique : [décrire le projet].
~~~

Le contenu généré utilise `locale: "fr"` par défaut. Utiliser `"en"` pour produire l’interface, les questions, les statuts, l’accessibilité et les exports en anglais.

---

<a id="english"></a>

## English

### What the plugin does

The plugin progressively frames websites, applications, games, online services, internal tools, automations, connected products and AI/data projects. It works with an early idea or a detailed brief and asks only questions that can materially change the product.

It produces:

- Visualize questionnaires inside the conversation, with selectable choices and clarification fields;
- free-form chat replies preserved by the agent, with complementary reading sheets when useful;
- a traceable decision register with assumptions and deferred decisions;
- a consolidated specification linked to decisions;
- one delivery plan with Kanban and roadmap reading views updated from the conversation;
- a button in the plan to return directly to the questions;
- verifiable archives of original replies and decisions.

The default workflow is to answer a Visualize questionnaire directly in the conversation using
selectable choices and clarification fields, then let the agent consolidate decisions. Free-form
chat replies are also accepted. If Visualize is unavailable, the agent uses visible native
questions or plain chat. Complementary `--read-only` sheets support reading and planning;
they have no answer fields or Send button and work without JavaScript.

### Preview

These screenshots illustrate standalone sheets; the default questionnaire now appears inside the conversation through Visualize.

#### Interactive questionnaire

![Interactive project questionnaire](plugins/concevoir-projet-interactif/assets/screenshots/questionnaire-en.png)

#### Actionable Kanban

![Interactive project Kanban](plugins/concevoir-projet-interactif/assets/screenshots/planning-kanban-en.png)

### Install from GitHub

Add the repository as a Git marketplace, then install the plugin:

~~~bash
codex plugin marketplace add nettyks/concevoir-projet-interactif --ref main
codex plugin add concevoir-projet-interactif@nettyks
~~~

Start a new Codex task afterwards so the plugin skill is loaded.

### Usage

~~~text
Use $concevoir-projet-interactif to frame this digital project: [describe the project].
~~~

Use `locale: "en"` for English output or `"fr"` for French output. Technical identifiers remain stable between both languages.

---

## Structure

~~~text
concevoir-projet-interactif/
├── .agents/plugins/marketplace.json
├── .github/workflows/tests.yml
├── plugins/
│   └── concevoir-projet-interactif/
│       ├── .codex-plugin/plugin.json
│       ├── assets/
│       ├── skills/
│       │   └── concevoir-projet-interactif/
│       │       ├── SKILL.md
│       │       ├── agents/
│       │       ├── assets/
│       │       ├── references/
│       │       └── scripts/
│       └── tests/
└── README.md
~~~

The repository is a Git marketplace containing one skill-only plugin. It does not require an MCP server or a remote application.
