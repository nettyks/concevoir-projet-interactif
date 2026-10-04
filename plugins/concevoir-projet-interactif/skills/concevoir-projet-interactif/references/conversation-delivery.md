# Répondre directement dans le chat

## Mode par défaut : questionnaire Visualize dans la conversation

Générer les questionnaires avec `--inline` et les afficher directement dans la conversation.
Lire le skill Visualize disponible et respecter son contrat de fragment. Préférer les choix
à cocher lorsque des options concrètes sont utiles et prévoir un champ de précision
(`allow_note: true`). Les questions de découverte utilisent un champ ouvert. Ne rien précocher.
La source JSON reste canonique pour les questions ; seuls les messages effectivement reçus
permettent de consolider les réponses.

Formuler les questions en langage courant et accepter aussi les réponses libres dans le chat, même si
elles ne suivent pas les choix ou l’ordre de la fiche. Ne pas demander à l’utilisateur de
recopier des identifiants, remplir du JSON ou retourner un fichier. Répondre aussi à ses questions
et adapter les propositions avant de poursuivre les points ouverts.

Conserver les messages exacts du répondant, datés et séparés, dans `conception/reponses-T01.md`
(adapter le tour). Enregistrer les correspondances avec les questions et les décisions dans
le registre ; une reformulation reste une interprétation, pas une citation. Si le message
nuance plusieurs propositions, conserver ces nuances au lieu de le forcer dans un choix.
Une absence de réponse reste ouverte. Ne pas archiver les messages sans rapport avec le projet.

À la clôture du tour, `project_artifacts.py archive --answers reponses-T01.md` accepte ce Markdown
brut et conserve son empreinte ; aucun export du répondant n’est nécessaire. Donner aussi le
chemin du fragment effectivement présenté au paramètre `--questionnaire` et le projet/tour aux paramètres habituels.
Archiver avant de remplacer la fiche ou commencer un nouveau tour. Une ancienne fiche contenant
des réponses possibles doit être conservée avant conversion ; ne pas effacer son stockage.

## Modes complémentaires et compatibilité

Le workflow du skill utilise `--inline` par défaut pour les questionnaires. Pour compatibilité,
le script sans option continue de produire une fiche autonome à remplir, sur demande explicite.
Les fiches `--read-only` restent disponibles comme supports de lecture et pour le planning : sans
champ de réponse, stockage navigateur ni envoi. Ne pas combiner `--inline` et `--read-only`.

## Choisir la surface

Dans une conversation compatible avec Visualize, employer `--inline` sans demander de confirmation.
Le bouton appelle le pont fourni par l’hôte, `window.openai.sendFollowUpMessage({prompt, title})`.
Il n’appelle aucun serveur et ne connaît aucun identifiant de fil, jeton ou chemin secret.
La conversation hébergeant le formulaire est la destination ; l’hôte peut demander confirmation.

Une fiche HTML autonome dans le navigateur n’expose pas ce pont. Sans Visualize, utiliser les
questions natives visibles si leurs formats conviennent ; sinon poser une question simple en texte.
Respecter une préférence explicite pour un autre mode. Ne pas simuler un envoi réussi et ne pas imposer d’installation pour une
question simple. La présence d’un cache de plugin seule ne prouve pas que le rendu est activé.

## Générer et afficher

Conserver les mêmes identifiants, types, choix et `storage_key` dans le JSON canonique. Ne pas
écraser une ancienne fiche ou un formulaire auquel l’utilisateur pourrait encore répondre.

```bash
python3 /chemin/du/skill/scripts/render_artifact.py questionnaire \
  --input /chemin/du/projet/conception/questionnaire.json \
  --output /repertoire/de/visualisation/explicitement/disponible/questions-projet.html \
  --inline
```

Le fichier est un fragment HTML autonome sous 1 Mo, sans accès réseau, et utilise les contrôles
de Visualize. L’afficher dans la réponse finale avec le chemin absolu réellement écrit :

```text
visualize{"path":"/repertoire/de/visualisation/questions-projet.html"}
```

Ne pas ouvrir ce fragment dans un onglet navigateur et ne pas le traiter comme un site à publier.
L’ancien mode sans `--inline` continue de produire `conception/questionnaire-actif.html`.
Une sauvegarde locale de cette ancienne fiche ne migre pas automatiquement vers Visualize :
préserver l’original, signaler cette limite si des réponses y sont déjà saisies, et proposer
l’import de sa sauvegarde JSON. La clé de stockage inline est préfixée par `conversation:`.

## Envoi et conservation

Le formulaire prend en charge texte, décision, choix unique ou multiple, échelle et classement.
Une échelle non touchée ou un classement non validé restent sans réponse. Les notes sont envoyées
avec les réponses, y compris lorsqu’elles nuancent un choix. Le bouton propose un envoi partiel
explicite s’il reste des réponses manquantes ou des choix demandant une précision.

L’envoi contient un résumé lisible et le JSON `project-workshop-answers-v2`, avec projet, tour,
clé de fiche, réponses brutes, notes et état de complétion. Le contenu est envoyé seulement au clic.
Un double clic en attente ne doit pas créer deux messages ; un message identique déjà accepté
ne doit pas être renvoyé. Après annulation ou erreur, garder les réponses et permettre de réessayer.
Ne jamais annoncer une réception en conversation sur la seule base d’un test avec un faux pont.
Le pont de certaines versions renvoie `undefined` après une annulation comme après un envoi :
afficher alors « Envoi demandé » et permettre un renvoi explicite après vérification du fil.
La résolution de la promesse ne prouve pas à elle seule que le message a été reçu.

Le stockage du navigateur est utilisé au mieux et n’est pas une sauvegarde durable ni chiffrée.
Si le pont est absent, afficher clairement un repli par copie du message. Si le presse-papiers
est refusé, afficher le texte sélectionnable. Les sauvegardes et imports JSON restent disponibles.
Les réponses trop volumineuses doivent être conservées puis réparties en tours ; aucune troncature.

## Consolider le message reçu

Vérifier projet, tour, clé de stockage, identifiants de questions et choix contre le JSON canonique.
Les champs `completion` du message sont indicatifs : recalculer les questions ouvertes à partir
des réponses et des règles de la fiche. Ne pas convertir une absence en Non ou Peut-être en Oui.

Écrire le bloc JSON brut reçu dans un nouveau fichier de réponses, puis utiliser la commande
`archive` habituelle avec le fragment et ce fichier. Elle conserve la fiche, le JSON et leurs
empreintes. Ajouter au journal que la source est un message envoyé depuis le formulaire.
Consolider ensuite le registre et la spécification. Aucun export manuel du répondant n’est requis.

## Sources de la capacité

Vérifiées le 10 septembre 2026 :

- Skill Visualize installé : section Composition, `sendFollowUpMessage({ prompt, title })`.
- [Disponibilité de Visualize](https://learn.chatgpt.com/docs/visualizations).
- [Pont des interfaces de plugins](https://developers.openai.com/plugins/build/chatgpt-ui#prefer-shared-fields-and-methods).

Le protocole MCP Apps `ui/message` concerne une interface hébergée par un plugin MCP. Ce skill
emploie le pont de Visualize déjà disponible et n’ajoute pas de serveur MCP pour ce seul besoin.
