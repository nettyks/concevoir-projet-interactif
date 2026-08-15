# Conventions des artefacts de conception

## Sommaire

- Arborescence canonique
- Responsabilité de chaque fichier
- Registre de décisions
- Cycle de vie d'une décision
- Archivage d'un tour
- Sources et preuves
- Spécification et planning
- Règles de sécurité et de reprise

## Arborescence canonique

Créer `conception/` dans le projet, sauf si une organisation existante remplit déjà les mêmes rôles :

```text
conception/
├── journal.md
├── decisions.json
├── sources.md
├── specification.md
├── questionnaire-actif.html
├── tours/
│   └── T01/
│       ├── questionnaire.html
│       ├── reponses-01.json
│       └── archive.json
└── planning/
    ├── plan.json
    └── plan.html
```

Ne pas créer une seconde source de vérité si le dépôt possède déjà des ADR, une spécification ou un registre de décisions. Documenter la correspondance dans `journal.md`.

## Responsabilité de chaque fichier

- `journal.md` : chronologie concise des tours, validations, changements et points ouverts.
- `decisions.json` : historique structuré, append-only par identifiant; seule source de vérité des décisions brutes et interprétées.
- `sources.md` : références externes, dates de vérification et distinction entre fait et inférence.
- `specification.md` : vue consolidée et lisible de l'état actuel; peut être brouillon ou validée.
- `questionnaire-actif.html` : fiche du tour en cours; jamais source de vérité après archivage.
- `tours/` : questionnaires et réponses brutes immuables.
- `planning/` : plan source JSON et fiche générée.

Ne pas ajouter de `README.md`, de duplicata du brief ou de document auxiliaire sauf demande explicite ou convention déjà présente dans le projet. Les artefacts canoniques ci-dessus suffisent normalement.

## Registre de décisions

Suivre `references/decisions.schema.json`. Chaque entrée utilise au minimum :

```json
{
  "id": "D-001",
  "kind": "decision",
  "status": "accepted",
  "title": "Le service sera accessible depuis un navigateur",
  "rationale": "Les utilisateurs ne veulent aucune installation.",
  "source_round": "T02",
  "source_questions": ["TECH-03"],
  "evidence": ["Réponse exportée du tour T02"],
  "confidence": "high",
  "owner": null,
  "priority": "indispensable",
  "supersedes": [],
  "created_at": "2026-08-16",
  "updated_at": "2026-08-16"
}
```

Valeurs de `kind` : `fact`, `decision`, `constraint`, `hypothesis`, `open_question`.

Valeurs de `status` :

- `proposed` : interprétation encore non validée;
- `accepted` : décision explicitement validée;
- `rejected` : proposition refusée;
- `deferred` : décision volontairement repoussée;
- `superseded` : remplacée par une nouvelle entrée.

Valeurs de `confidence` : `verified`, `high`, `medium`, `low`, `unknown`. `verified` exige une preuve identifiée, pas seulement une impression.

Valeurs facultatives de `priority` : `indispensable`, `important`, `differable`. Ne pas attribuer une priorité silencieusement.

## Cycle de vie d'une décision

1. Conserver la réponse brute dans le dossier du tour.
2. Créer une entrée `proposed` lorsque l'interprétation nécessite encore une validation.
3. Passer à `accepted`, `rejected` ou `deferred` après décision explicite.
4. Ne jamais réécrire rétroactivement une décision changée.
5. Créer une nouvelle entrée, renseigner `supersedes`, puis passer l'ancienne à `superseded`.
6. Mettre à jour la spécification pour montrer uniquement l'état consolidé tout en gardant l'historique dans le registre.

Un choix « Peut-être » ou une absence de réponse ne produit jamais une décision `accepted`.

## Archivage d'un tour

Utiliser une `round_id` stable (`T01`, `T02`...) et une `storage_key` différente par tour. Archiver avant de remplacer la fiche active.

Le script `project_artifacts.py archive` :

- refuse un identifiant dangereux ou un dossier d'archive déjà existant;
- copie la fiche et un ou plusieurs exports;
- calcule les empreintes SHA-256;
- écrit `archive.json` avec la date réelle d'archivage;
- ajoute l'événement au journal.

Ne pas modifier le contenu d'un tour archivé. En cas de correction, créer un nouveau tour ou une note explicite dans le journal.

Écrire les entrées du journal après l'action correspondante. Une ligne telle que « plan validé et HTML généré » n'est permise qu'après présence des deux fichiers et réussite du générateur.

## Sources et preuves

Pour chaque recherche structurante, enregistrer : titre, URL ou chemin, organisme/auteur, date de consultation, décision concernée et nature de l'usage.

Étiqueter l'usage :

- **fait vérifié** : directement soutenu par la source;
- **inférence** : conclusion raisonnable mais non déclarée explicitement;
- **inspiration** : idée issue d'un autre produit, sans preuve d'adéquation.

Ne pas recopier un secret, une clé, un jeton ou une donnée personnelle inutile dans les sources, le journal ou une fiche HTML.

## Spécification et planning

La spécification porte un statut visible : `brouillon`, `à valider` ou `validée`. Seule une validation explicite autorise `validée`.

Chaque exigence reçoit un identifiant stable (`REQ-001`) et référence les décisions qui la justifient. Chaque segment du planning utilise `decision_refs` ou les identifiants d'exigence correspondants.

Le plan JSON est canonique pour sa structure. Les changements d'état effectués dans le Kanban sont une couche locale jusqu'à leur export et leur consolidation dans `plan.json`.

## Règles de sécurité et de reprise

- La sauvegarde navigateur et les exports ne sont pas chiffrés.
- Ne jamais demander de mot de passe, clé privée, jeton ou secret dans un questionnaire.
- Exporter le JSON à la fin de chaque tour important; `localStorage` n'est pas une sauvegarde durable.
- Vérifier projet, tour, schéma et clé de stockage avant tout import.
- Ne jamais écraser un original avec un HTML généré; utiliser des chemins distincts.
- Préférer une écriture atomique et refuser un conflit de fichier plutôt que deviner l'intention.

Les fiches ciblent un navigateur moderne prenant en charge JavaScript ES2021, `localStorage`, `Blob`, `URL.createObjectURL`, `CSS.escape` et l'élément `<dialog>`. Elles doivent rester utilisables sans réseau; le stockage local doit disposer d'un mode dégradé explicite lorsqu'il est refusé ou saturé.
