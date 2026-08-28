# Cadre de réalisation d'un projet numérique

## Langue du plan

Utiliser `locale: "fr"` ou `locale: "en"`. Le modèle traduit l'interface, les états par défaut, les sévérités affichées, les messages et l'export Markdown. Rédiger dans la même langue les titres, objectifs, livrables, critères, risques, questions et jalons.

Conserver les identifiants techniques lors d'une traduction : phases, segments, décisions, statuts (`a-preciser`, `pret`, `en-cours`, `verification`, `termine`) et sévérités (`bloquant`, `avant-segment`, `differable`). Ils restent indépendants de la langue et garantissent la compatibilité des dépendances et des états sauvegardés. Consulter `planning-example.en.json` pour un exemple complet.

## Source de vérité après validation

Maintenir une spécification courte contenant vision, utilisateurs, parcours essentiels, périmètre, hors périmètre, exigences techniques, risques, hypothèses, décisions différées et critères de réussite. Relier chaque exigence à ses décisions d'origine.

Le registre `conception/decisions.json` conserve l'historique; la spécification présente l'état consolidé. Un plan ne doit pas réintroduire une décision refusée ou remplacée.

## Définition d'un segment

Un segment est une unité de résultat, pas une catégorie technique. Le contrat V2 exige :

- `id` stable;
- titre orienté résultat;
- `objective` utilisateur ou opérationnel;
- phase et `order` explicites;
- état actuel;
- `decision_refs` vers les décisions réalisées;
- livrables observables;
- prérequis externes;
- dépendances internes par identifiant;
- critères d'acceptation vérifiables;
- risques et inconnues;
- questions ouvertes localisées.

`owner`, `effort` et `priority` sont facultatifs et ne doivent apparaître que si l'utilisateur les a fournis ou validés. Préférer « Un utilisateur invité peut créer et retrouver un dossier » à « Faire le backend ».

## Construire l'ordre logique

1. Identifier les preuves ou décisions capables d'invalider le projet.
2. Placer les fondations minimales réellement nécessaires.
3. Construire un premier parcours complet et testable de bout en bout.
4. Ajouter les capacités partagées avant les fonctions qui les consomment.
5. Traiter sécurité, sauvegarde, observabilité et accessibilité dans les segments concernés.
6. Ajouter fonctions secondaires et optimisation après preuve du parcours principal.
7. Préparer distribution, migration et exploitation avant l'ouverture au public visé.

Déclarer toutes les dépendances. Aucun cycle n'est autorisé. Une dépendance doit être dans une phase antérieure ou dans la même phase avec un `order` inférieur. Deux segments d'une même phase ne partagent pas le même ordre.

L'ordre d'affichage doit rester déterministe : phase par `order`, puis segment par `order`. Ne jamais dépendre implicitement de l'ordre d'écriture du JSON.

## Jalons adaptables

- **Clarification risquée** : recherche, prototype ou test de faisabilité.
- **Socle minimal** : structure et données strictement nécessaires au premier parcours.
- **Première tranche utile** : parcours principal complet.
- **Fiabilisation** : erreurs, sécurité, sauvegarde, performances et accessibilité.
- **Élargissement** : fonctions secondaires, collaboration et intégrations.
- **Mise à disposition** : distribution, migration, documentation, support et exploitation.
- **Évolution** : mesures, retours, réversibilité et prochains incréments.

Adapter ces jalons; ne pas les imposer à un petit projet.

## États Kanban

Valeurs par défaut :

- `a-preciser`
- `pret`
- `en-cours`
- `verification`
- `termine`

Des colonnes personnalisées sont possibles si elles sont déclarées. Chaque segment doit appartenir à une colonne existante. Une carte bloquée nomme son blocage dans les questions ou prérequis.

La fiche Kanban V2 permet de changer un état au clavier, le sauvegarde localement et exporte l'état. Le JSON de plan reste le point de départ canonique; un export d'état doit être consolidé avant de remplacer ce fichier.

## Roadmap horizontale

La roadmap montre trajectoire, jalons, ordre et dépendances. Sans dates ou estimations validées, employer des noms de phases relatifs, jamais de fausses dates.

Kanban et roadmap partagent exactement les mêmes segments. La propriété `view` choisit seulement la vue initiale; l'utilisateur peut basculer dans la fiche sans générer un second plan.

La barre d'actions du plan propose aussi « Afficher les questions » / « View questions ». Ce bouton revient vers `conception/questionnaire-actif.html` avec le lien relatif `../questionnaire-actif.html`; conserver l'arborescence canonique pour garantir ce fonctionnement hors ligne.

## Questions ouvertes

Afficher un panneau « À préciser avec l'utilisateur ». Utiliser les sévérités :

- `bloquant` : requis avant de commencer;
- `avant-segment` : requis avant le segment indiqué;
- `differable` : amélioration non bloquante.

Ne pas bloquer tout le projet pour une question localisée. Rattacher la question au segment concerné.

## Critères de qualité

- Chaque décision acceptée destinée à cette version apparaît dans `decision_refs` d'au moins un segment.
- Aucune décision refusée ou remplacée ne réapparaît comme travail.
- Chaque segment produit un résultat vérifiable et possède au moins un livrable et un critère d'acceptation.
- Chaque dépendance pointe vers un segment existant et respecte l'ordre des phases.
- Aucun segment ne disparaît d'une vue à cause d'une phase ou d'un état inconnu.
- Les prérequis, risques, questions, jalons et références restent présents dans l'export Markdown et JSON.
- Les hypothèses et points ouverts restent visibles.
- Le premier jalon produit une preuve utile, pas uniquement une pile technique.
- Le plan n'affirme pas être validé tant que le cadrage ne l'est pas explicitement.
