---
name: concevoir-projet-interactif
description: Cadrer progressivement un projet numérique avec des questionnaires Visualize directement dans la conversation, en français ou en anglais. Utiliser pour explorer une idée de site, application, jeu, service, automatisation ou projet IA, comparer des options, consolider les décisions et produire une spécification traçable puis un plan Kanban ou roadmap si demandé.
---

# Concevoir un projet numérique interactif

Transformer une idée numérique en décisions explicites et en artefacts maintenables. Adapter la profondeur au besoin; chaque niveau de sortie constitue un résultat valable.

## Principes

- Inspecter l'existant et préserver la terminologie ainsi que la source de vérité du projet.
- Classer silencieusement l'idée comme vague, intermédiaire ou précise; ne questionner que ce qui change réellement le produit.
- Commencer compact, puis ouvrir un nouveau tour uniquement lorsqu'une réponse révèle une décision utile.
- Employer le bon type de réponse : texte ouvert pour découvrir, choix neutre pour comparer, décision Oui/Non/Peut-être pour valider une proposition, sélection multiple, échelle ou classement pour arbitrer.
- Ne jamais interpréter « Peut-être », « Je ne sais pas » ou « À décider plus tard » comme une validation.
- Traiter une note comme prioritaire lorsqu'elle nuance un choix et conserver la réponse brute à côté de l'interprétation.
- Séparer faits vérifiés, décisions acceptées, refus, hypothèses, décisions différées, contradictions et points ouverts.
- Ne pas inventer de date cible, budget, capacité d'équipe, responsable ni estimation. Employer des phases relatives tant que ces données manquent.
- Déduire un thème lisible du domaine; ne demander une préférence visuelle qu'en présence d'une charte, d'une marque ou d'une contrainte d'accessibilité.
- Produire les fiches dans la langue de la demande, ou dans la langue explicitement choisie. Utiliser `locale: "fr"` ou `locale: "en"` et ne pas mélanger les langues dans les contenus destinés à l'utilisateur.
- Ne jamais demander ni stocker de secret dans une fiche. Signaler que la sauvegarde navigateur et les exports ne sont pas chiffrés si les réponses peuvent être sensibles.
- Ne jamais annoncer dans le journal ou la synthèse qu'un artefact est créé, validé ou testé avant que le fichier existe et que le contrôle correspondant ait réellement réussi.

## Choisir le niveau de sortie

Déduire le niveau attendu de la demande et accepter explicitement les points d'arrêt suivants :

1. **Exploration** : clarifier le problème, le public, la valeur et les inconnues principales. Produire le journal, le registre de décisions et les tours archivés.
2. **Cadrage** : ajouter le périmètre fonctionnel, les arbitrages, les risques structurants et les choix techniques; produire une spécification marquée brouillon ou validée.
3. **Réalisation** : lorsque le cadrage est validé ou que la demande actuelle fournit un brief
   suffisamment précis et demande explicitement l’implémentation, segmenter le développement et
   produire uniquement le pilotage utile.

Sans demande explicite, commencer en exploration et proposer la suite seulement si elle apporte une valeur immédiate. Une demande courte ne doit pas déclencher automatiquement tout le parcours.

Pour un brief précis dont les décisions sont explicitement données comme validées, ne pas générer de questionnaire de confirmation. Enregistrer une entrée concise par décision fournie, limiter les hypothèses nouvelles aux éléments indispensables, puis produire d'abord la spécification utile et le plan demandé. Ne pas retarder le livrable principal par une documentation exhaustive non demandée.

## Initialiser les artefacts

Lire `references/artifact-conventions.md` avant de créer ou reprendre les fichiers de conception. Utiliser le script sans écraser l'existant :

```bash
python3 /chemin/du/skill/scripts/project_artifacts.py init \
  --project-dir /chemin/du/projet --title "Nom du projet" --slug nom-du-projet
```

Le dossier `conception/` contient le journal, le registre de décisions, les sources, la spécification, les tours et le planning. Si le projet possède déjà une organisation équivalente, la conserver et documenter la correspondance au lieu de créer un doublon.

## Recueillir les réponses dans la conversation

Par défaut, présenter les questions dans un **formulaire Visualize intégré à la conversation**,
avec des choix à cocher lorsque le sujet s’y prête et un champ de précision (`allow_note: true`).
Utiliser un champ ouvert lorsqu’il faut découvrir un besoin. Lire les instructions du skill
Visualize disponible avant de créer le fragment et employer le rendu `--inline`.

Avancer par petits tours centrés sur les décisions utiles ; poser une seule question si la suite
en dépend. Le répondant peut aussi écrire librement dans le chat, nuancer ou regrouper ses réponses,
sans syntaxe ni identifiants imposés. Ne pas précocher une décision ni exiger un export manuel.

Si Visualize est indisponible ou si l’utilisateur demande un autre mode, employer les questions
natives visibles du chat ou une question en texte simple. Ne pas imposer d’installation ni
remplacer silencieusement le formulaire intégré par une page dans le navigateur.
Les fiches `--read-only` restent des supports complémentaires de lecture, notamment pour le plan.

Conserver les messages bruts, les relier aux questions concernées puis mettre à jour décisions,
spécification et fiches à partir des réponses certaines. Clarifier uniquement les ambiguïtés qui
changeraient une décision. L’utilisateur n’a pas à produire lui-même de JSON.

Lire [references/conversation-delivery.md](references/conversation-delivery.md) pour l’affichage,
l’envoi, les replis et l’archivage. Afficher le fragment dans la réponse finale du même tour.
Pour les fiches de lecture complémentaires, utiliser `open_in_codex`, cible `browser` et URL `file://` absolue,
lorsque la politique l’autorise. En cas de blocage, fournir le lien local sans contournement.

## Conduire les tours de cadrage

### 1. Examiner le contexte et les risques

Repérer les documents canoniques, les décisions existantes et les contraintes certaines. Faire dès le premier tour un triage des inconnues capables d'invalider le projet : réglementation, données sensibles, API imposée, matériel, stores, charge, sécurité, coût récurrent ou faisabilité critique.

Lire `references/question-framework.md`, puis sélectionner uniquement les catégories pertinentes. Une vérification courte peut être faite directement. Annoncer toute délégation de recherche; demander une autorisation seulement si elle entraîne un coût, une écriture externe, une action distante sensible ou sort du périmètre déjà confié.

### 2. Générer une fiche adaptée

Construire un JSON conforme à `references/questionnaire.schema.json` et s'inspirer de `references/questionnaire-example.json` :

Conserver les questions structurées dans `conception/questionnaire.json` et générer le formulaire
Visualize avec `--inline` dans le répertoire de visualisation explicitement disponible pour le fil.
Une question autonome sans choix peut être posée directement si un formulaire n’apporte rien.

```bash
python3 /chemin/du/skill/scripts/render_artifact.py questionnaire \
  --input /chemin/du/projet/conception/questionnaire.json \
  --output /repertoire/de/visualisation/explicitement/disponible/questions-projet.html --inline
```

Relire le fragment généré puis l’afficher selon `references/conversation-delivery.md`, sans ouvrir
d’onglet navigateur. Une fiche complémentaire `conception/questionnaire-actif.html` peut être
générée avec `--read-only`, notamment comme destination du lien de retour depuis le planning.

Pour une fiche anglaise, utiliser `locale: "en"` et `references/questionnaire-example.en.json`. Le modèle traduit automatiquement l'interface, les messages, les contrôles d'accessibilité et l'export Markdown; traduire aussi les titres, descriptions, choix et textes d'aide du JSON. Conserver les identifiants de questions et de choix lors de la traduction d'une fiche existante afin de préserver la compatibilité des réponses.

Utiliser une nouvelle `round_id` et une nouvelle `storage_key` à chaque tour. Employer des identifiants stables et sûrs. Les choix personnalisés doivent rester visuellement neutres sauf si leur couleur exprime réellement un état; utiliser `needs_clarification` indépendamment de `tone`.

### 3. Consolider et archiver

À chaque message de réponses reçu :

1. conserver le texte exact du message dans les réponses brutes du tour, sans le remplacer par une reformulation;
2. relier les passages aux questions et distinguer cette interprétation de la réponse brute; conserver les réponses non sollicitées pertinentes;
3. mettre à jour `decisions.json` avec source, justification, preuve, confiance et éventuel remplacement d'une décision antérieure;
4. mettre à jour le journal, les sources et les points ouverts;
5. relever contradictions et réponses différées;
6. préparer uniquement les nouvelles questions nécessaires.

```bash
python3 /chemin/du/skill/scripts/project_artifacts.py archive \
  --project-dir /chemin/du/projet --round-id T01 \
  --questionnaire /repertoire/de/visualisation/explicitement/disponible/questions-projet.html \
  --answers /chemin/du/projet/conception/reponses-T01.md
```

Archiver le fragment effectivement présenté pour ce tour, le JSON de questions et les réponses
brutes reçues avant de préparer le suivant. Un clic ou un test du pont d’envoi ne prouve pas la
réception : attendre le message dans la conversation. Une fiche active ou remplacée n'est jamais
la source de vérité : le registre de décisions et la spécification le deviennent après consolidation.

## Cadrer la réalisation technique

Ne pas attendre artificiellement la fin du fonctionnel lorsqu'une contrainte technique peut changer le produit. Sinon, ouvrir le tour technique après avoir compris l'usage.

- Réutiliser les choix techniques déjà documentés et demander leur caractère obligatoire, préféré ou envisagé seulement si cela manque.
- Sans choix préalable, présenter deux à quatre scénarios en langage courant : ce que c'est, adapté si, moins adapté si, entretien, coût probable et recommandation justifiée.
- Examiner seulement les sujets applicables : plateformes, audience et simultanéité, comptes et rôles, données, intégrations, hors-ligne, compatibilité, accessibilité, sécurité, confidentialité, exploitation, sauvegarde/restauration, distribution, coûts et réversibilité.
- Ajouter un arbitrage explicite du périmètre : indispensable, important, différable ou refusé; employer un classement lorsque tout ne peut pas être prioritaire.

## Valider et spécifier

Présenter une synthèse courte séparant : décidé, refusé, à confirmer, hypothèses et contradictions.
Demander une validation explicite avant de marquer une spécification comme validée. Pour lancer
l’implémentation, une demande explicite fondée sur un brief précis ou une spécification déjà
acceptée constitue cette autorisation ; ne pas imposer un tour de confirmation supplémentaire.
Lorsqu’une décision manquante change matériellement le produit, réaliser d’abord ce qui n’en dépend
pas puis demander uniquement l’arbitrage nécessaire. Un brouillon peut être produit sans validation
s’il est clairement étiqueté.

La spécification doit relier chaque exigence à une ou plusieurs décisions du registre et contenir vision, utilisateurs, parcours essentiels, périmètre, hors périmètre, exigences techniques, risques, hypothèses, décisions différées et critères de réussite.

Rester proportionné : détailler ce qui influence le produit ou un segment, mais ne pas inventer un modèle complet, une architecture ou des règles secondaires pour remplir le document.

## Segmenter la réalisation

Après validation, lire `references/delivery-framework.md`. Construire un JSON conforme à `references/planning.schema.json` et à `references/planning-example.json`.

Pour un plan anglais, utiliser `locale: "en"` et `references/planning-example.en.json`. Conserver les identifiants techniques de statuts et de sévérités (`a-preciser`, `avant-segment`, etc.); la fiche les présente automatiquement en anglais.

Chaque segment doit produire un résultat vérifiable et référencer les décisions qu'il réalise. Déclarer objectif, livrables, prérequis, dépendances, ordre, critères d'acceptation, risques et questions ouvertes. Favoriser une première tranche utilisable de bout en bout; intégrer sécurité, accessibilité, sauvegarde et observabilité dans les segments concernés.

Déduire la vue initiale : Kanban pour piloter l'état, roadmap pour expliquer la trajectoire. Ne pas imposer une question supplémentaire, car la fiche permet de basculer entre les deux vues.

```bash
python3 /chemin/du/skill/scripts/render_artifact.py planning \
  --input /chemin/du/projet/conception/planning/plan.json \
  --output /chemin/du/projet/conception/planning/plan.html --read-only
```

Le Kanban et la roadmap affichent l’état issu de `plan.json` en lecture seule. Les changements
se demandent dans le chat ; l’agent met à jour la source puis régénère la fiche. Sans calendrier
validé, utiliser des phases relatives.

La fiche de planning contient un lien bilingue vers `../questionnaire-actif.html` pour relire
les propositions et questions. Respecter l’arborescence canonique pour que ce lien fonctionne.

## Vérifier avant remise

- Exécuter les tests : `python3 -m unittest discover -s tests -v`.
- Générer les exemples de questionnaire avec `--inline` ; vérifier les choix, champs de précision, langue et conservation des réponses. Vérifier aussi les vues complémentaires `--read-only` si elles sont modifiées.
- Vérifier que le texte brut d’une réponse libre s’archive intact, sans imposer un choix ou une validation qui n’a pas été exprimé.
- Afficher les questionnaires Visualize dans la réponse finale ; ne pas ouvrir leurs fragments dans un navigateur. Ouvrir les fiches de lecture complémentaires lorsque la politique l’autorise ; distinguer contrôles statiques et vérification visuelle.
- Vérifier le lien du planning vers `questionnaire-actif.html` et les exemples français/anglais.
- Vérifier qu'aucune question, carte, dépendance ou information d'export ne disparaît silencieusement.
- Vérifier clavier, mobile, impression et cohérence des archives selon le changement. Tester les fonctions de saisie et d’envoi lorsqu’elles sont modifiées, sans confondre un pont simulé avec une réception réelle.
- Exécuter le validateur de skill après toute modification structurelle.

## Ressources

- `references/question-framework.md` : routage des questions et types de réponses.
- `references/delivery-framework.md` : segmentation, ordre, vues et critères de qualité.
- `references/artifact-conventions.md` : arborescence, registre de décisions, sources et cycle de vie.
- `references/conversation-delivery.md` : questionnaires Visualize par défaut, réponses libres, envoi et archivage.
- `references/*.schema.json` : contrats V2 exécutables pour questionnaire et planning, avec `locale` français ou anglais.
- `scripts/render_artifact.py` : questionnaires Visualize (`--inline`), fiches de lecture (`--read-only`) et formulaires autonomes sur demande.
- `scripts/project_artifacts.py` : initialisation et archivage sans écrasement.
- `assets/*-template.*` : fiches et documents canoniques.
