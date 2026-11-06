Mission complète : création du projet iOS-tegu à partir d’un firmware iOS 27

Tu dois travailler directement dans Freebuff Cloud, en utilisant le dépôt GitHub déjà connecté. Toute la mission doit être réalisée dans l’environnement cloud, sans demander à l’utilisateur d’effectuer manuellement les étapes techniques.

Le nom officiel et obligatoire du projet est :

iOS-tegu

Ce nom doit être utilisé partout : nom du projet, dossiers, documentation, configuration, scripts, README et éventuels noms de releases. Ne le remplace jamais par un autre nom.

1. Source du firmware

À la racine du dépôt GitHub, ouvre le fichier ROM.MD.

Ce fichier contient un lien MEGA permettant d’accéder au firmware iOS 27 au format IPSW.

Tu dois :

1. Lire ROM.MD.
2. Récupérer le lien MEGA qu’il contient.
3. Accéder au fichier IPSW depuis l’environnement cloud.
4. Télécharger le firmware intégralement dans le stockage temporaire du cloud.
5. Vérifier que le téléchargement est terminé et que le fichier n’est pas incomplet.
6. Identifier le modèle d’iPhone, la version iOS et le numéro de build correspondant exactement au firmware téléchargé.

Si MEGA demande une autorisation, une clé, une connexion ou une confirmation que tu ne possèdes pas, arrête-toi et indique précisément ce qui manque. Ne prétends jamais avoir téléchargé le firmware si ce n’est pas le cas.

2. Extraction et analyse du firmware

Après le téléchargement :

* Analyse le fichier IPSW.
* Identifie son contenu et les différentes images système.
* Extrais les fichiers accessibles avec les outils compatibles.
* Analyse les composants du système, les fichiers de démarrage, les informations matérielles et les métadonnées.
* Identifie les composants XNU, le système de fichiers, les bibliothèques, les frameworks et les composants nécessaires au démarrage.
* Conserve les noms et structures d’origine lorsqu’ils sont utiles.
* Documente les éléments qui sont chiffrés, signés ou qui nécessitent des outils ou autorisations supplémentaires.

Attention : un simple décompactage ZIP ne signifie pas que le système iOS a été entièrement extrait. Ne contourne aucune protection cryptographique ou signature Apple. Ne fabrique pas de fichiers manquants et ne prétends pas avoir extrait des composants auxquels tu n’as pas réellement accès.

3. Objectif technique : iOS sur Pixel 9a

Le projet iOS-tegu a pour objectif d’étudier et de développer un véritable portage expérimental d’iOS sur le Google Pixel 9a, dont le nom de code est tegu et qui utilise le processeur Google Tensor G4.

Il ne s’agit absolument pas de créer un launcher Android, un thème ou une simple imitation visuelle d’iOS.

L’objectif est d’étudier la possibilité de faire fonctionner un véritable environnement système basé sur XNU et les composants iOS compatibles, sur le matériel du Pixel 9a.

Étudie notamment :

* La compatibilité entre le noyau XNU et le Tensor G4.
* La chaîne de démarrage du Pixel 9a.
* Le bootloader et les mécanismes de démarrage.
* Le device tree et la description du matériel.
* La gestion de la mémoire et des interruptions.
* Les pilotes nécessaires à l’écran, au tactile, au stockage et aux autres composants.
* Les possibilités d’adaptation des composants système.
* Les différences entre le matériel Apple et celui du Pixel 9a.

Ne suppose jamais que le firmware d’un iPhone est directement compatible avec le Pixel 9a. Le travail doit reposer sur une analyse technique réelle.

4. Organisation du projet

Crée une structure propre et professionnelle pour iOS-tegu.

Proposition d’organisation à adapter selon les fichiers réellement disponibles :

* firmware/ : métadonnées et éléments dont la redistribution est autorisée.
* kernel/ : recherches et travaux relatifs au noyau.
* boot/ : études sur la chaîne de démarrage.
* device/tegu/ : informations matérielles du Pixel 9a.
* drivers/ : recherches et développements de pilotes.
* tools/ : scripts et outils du projet.
* docs/ : documentation technique.
* checksums/ : sommes de contrôle des fichiers.
* README.md : présentation générale du projet.

Adapte cette structure si nécessaire. Ne crée pas de dossiers remplis de fichiers vides uniquement pour donner l’impression que le projet avance.

5. Publication GitHub : règle obligatoire

Tu dois appliquer une règle stricte pour choisir entre le dépôt GitHub et une GitHub Release.

Analyse la taille de tous les fichiers extraits destinés à être publiés et dont la redistribution est autorisée.

Cas A : tous les fichiers respectent les limites du dépôt

Si chaque fichier publiable respecte individuellement la limite de taille applicable au dépôt GitHub :

* Place les fichiers dans le dépôt.
* Organise-les dans l’arborescence de iOS-tegu.
* Crée un commit propre.
* Publie les changements sur le dépôt connecté.

Cas B : au moins un fichier dépasse la limite du dépôt

Si un seul fichier publiable dépasse la limite applicable au dépôt :

* Ne place aucun des fichiers extraits destinés à la publication directement dans le dépôt.
* Regroupe tous les fichiers extraits publiables dans une seule GitHub Release.
* Ne mélange jamais les deux méthodes.
* Le dépôt doit contenir uniquement les scripts, la documentation, les métadonnées et les informations nécessaires pour retrouver et comprendre la Release.

Important : vérifie également les limites de taille applicables aux fichiers joints à une GitHub Release. Si un fichier dépasse aussi ces limites, ne le découpe pas automatiquement et ne prétends pas qu’il a été publié. Conserve-le dans un stockage cloud autorisé et indique clairement où se situe le blocage.

Cette règle de publication ne t’autorise jamais à redistribuer des composants propriétaires.

6. Respect des licences et de la propriété intellectuelle

Les composants du firmware Apple peuvent être propriétaires.

* Ne publie aucun composant propriétaire Apple sans autorisation de redistribution.
* Ne considère pas qu’un dépôt privé autorise automatiquement cette redistribution.
* Ne publie pas de clés, secrets, identifiants ou données confidentielles.
* Publie uniquement les fichiers dont la redistribution est autorisée.
* Pour les autres composants, conserve uniquement les informations techniques non confidentielles, les références, les sommes SHA-256 et les scripts originaux lorsque cela est permis.

Si un fichier ne peut pas être publié légalement, exclue-le de la publication et explique pourquoi dans le rapport final.

7. Documentation

Crée un README.md professionnel pour iOS-tegu.

Il doit expliquer :

* La présentation du projet.
* Son objectif technique.
* Le matériel ciblé : Pixel 9a (tegu, Tensor G4).
* Le firmware analysé : modèle, version iOS et build, uniquement après vérification.
* La structure du projet.
* Les composants réellement extraits et analysés.
* Les éléments encore manquants.
* Les difficultés de compatibilité.
* Les travaux réalisés et les prochaines étapes.
* Les limites légales et techniques.

Ajoute également des sommes SHA-256 pour les fichiers concernés et un rapport détaillé de l’analyse du firmware.

8. Autonomie de travail

Travaille de manière autonome dans Freebuff Cloud.

Tu n’as pas besoin de demander à l’utilisateur de valider chaque étape. Prends les décisions techniques raisonnables, réalise les analyses et les opérations possibles, puis passe à l’étape suivante.

En revanche :

* Vérifie techniquement les résultats avant de les utiliser.
* Ne simule jamais un téléchargement, une extraction, une compilation ou un test.
* Ne supprime pas les fichiers existants du dépôt sans nécessité.
* Ne remplace pas les fichiers utiles sans avoir vérifié leur contenu.
* Ne lance aucune opération de flash sur un appareil physique.
* Ne modifie pas le Pixel 9a.
* Ne présente jamais une fonctionnalité comme fonctionnelle sans preuve.

Si une étape est impossible, continue les autres tâches indépendantes et documente précisément le blocage.

9. Rapport final obligatoire

À la fin, fournis un rapport indiquant :

1. Si le lien MEGA a fonctionné.
2. Si le firmware IPSW a été téléchargé intégralement.
3. Le modèle d’iPhone, la version iOS et le build identifiés.
4. Les éléments réellement extraits et analysés.
5. La structure créée pour iOS-tegu.
6. Les fichiers publiés et leur emplacement.
7. La méthode de publication utilisée : dépôt GitHub ou une seule Release.
8. Les éventuels fichiers non publiés et les raisons.
9. Les analyses de compatibilité avec le Pixel 9a.
10. Les prochaines étapes techniques nécessaires.

Objectif final : construire une base de travail technique sérieuse, documentée et organisée pour le projet iOS-tegu, à partir du firmware iOS 27 fourni par le lien MEGA dans ROM.MD, en travaillant directement dans Freebuff Cloud.
