# Veille concurrentielle FSS/FSF

Outil personnel pour suivre le nombre de boutiques en propre (FSS/FSF -
Free Standing Store/Flagship, **pas** les corners multi-marques ni les
distributeurs wholesale) des marques de parfumerie de niche concurrentes,
classées par région (EMEA, UK, NOAM, LATAM, CHINA, APAC).

Esprit du projet : le plus simple qui marche. Stdlib d'abord, un fichier de
config (`brands.yaml`), un `if/elif` par type de scraper plutôt qu'un
système de plugins, pas de base de données tant qu'on n'en a pas besoin.

## Installer

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# éditer .env : identifiants Gmail (mot de passe d'application, pas le
# mot de passe principal), destinataire du rapport, etc.
```

`playwright` est dans `requirements.txt` mais n'est utilisé que si une
future marque `js_widget` n'expose aucune API JSON (dernier recours). Il
n'est pas nécessaire pour les marques actuellement dans `brands.yaml` - pas
la peine de lancer `playwright install chromium` avant d'en avoir besoin.

## Lancer

```bash
python run_report.py                        # toutes les marques
python run_report.py --brands mfk,diptyque  # seulement certaines (utile pour tester)

# Recoupement avec le vrai fichier de suivi + sans envoi d'email (test/dry-run) :
python run_report.py \
  --brands diptyque \
  --existing-file "/mnt/data/BIBLE KP & FM Distribution List.xlsx" \
  --no-email
```

Chaque exécution :
1. Scrape les store locators (`brands.yaml`), avec délai de 1-2s entre
   requêtes et respect du `robots.txt`.
2. Filtre mono-marque (FSS) vs wholesale via `known_retailers_blocklist.json`
   + un mot-clé sur le nom de la marque ; toute décision douteuse est
   loggée dans `_a_verifier.csv` plutôt que tranchée en silence.
3. Classe par région, calcule le total par marque, compare avec le relevé
   précédent (`data/snapshots/`) et calcule une tendance simple sur
   l'historique.
4. Recoupe avec le fichier de suivi existant si `--existing-file` (ou la
   variable d'environnement `COMPETITION_EXPORT_CSV`) est fourni - voir
   "Recoupement avec le fichier BIBLE existant" ci-dessous pour le détail.
5. Télécharge une photo pour chaque nouvelle boutique détectée quand le
   scraper en a trouvé une (`photos/{slug}/`), sinon laisse un placeholder
   `.txt` à compléter à la main.
6. Génère un brouillon d'email pour les équipes régionales
   (`drafts/regional_email_YYYY-MM-DD.txt`) listant les marques restées
   bloquées (échec technique ou pas de scraper fiable) - **jamais envoyé
   automatiquement**, à relire et envoyer soi-même.
7. Écrit `report_YYYY-MM-DD.csv` / `.xlsx` (colonnes `BRAND | EMEA | UK |
   NOAM | LATAM | CHINA | APAC | TOTAL | SOURCE | DATE`, prêtes à copier
   dans la BIBLE) et m'envoie le tout par email (tableau HTML + pièce
   jointe), si `GMAIL_ADDRESS` / `GMAIL_APP_PASSWORD` / `REPORT_RECIPIENT`
   sont renseignés dans `.env` - sinon le rapport reste disponible en local
   et le script le signale clairement au lieu d'échouer. Passer `--no-email`
   pour ne jamais envoyer (tests, dry-run), même si `.env` est configuré.

Un scraper qui échoue (site changé, blocage anti-bot) n'interrompt jamais
le reste du run : la marque apparaît en `[ECHEC]` dans le rapport avec le
message d'erreur, plutôt qu'un chiffre à zéro silencieux.

## Recoupement avec le fichier BIBLE existant

`--existing-file` accepte deux formats, choisis automatiquement selon
l'extension :

- **`.xlsx`** (le vrai fichier, ex. `BIBLE KP & FM Distribution List.xlsx`) :
  lu directement depuis l'onglet `Competition`, traité comme une base de
  données **par porte** (une ligne = une boutique physique), pas comme un
  tableau de synthèse régionale. Le fichier original **n'est jamais modifié**
  (ouverture en lecture seule, aucun `.save()`).
- **`.csv`** (ancien format `BRAND|EMEA|UK|NOAM|LATAM|CHINA|APAC|TOTAL|SOURCE|DATE`) :
  conservé pour compatibilité ascendante avec les exports de synthèse
  précédents.

### Colonnes attendues dans l'onglet `Competition`

`BRAND | REGION | COUNTRY | CITY | DOOR NAME | DOOR TYPE | OFF/Online | RETAILER | DOOR COUNT`

### Nettoyage avant comparaison

Chaque valeur (marque, région, pays, ville, nom de porte) est normalisée
(`normalize.py` : minuscules, accents retirés, ponctuation et espaces
superflus supprimés) avant toute comparaison, pour que "Saint-Honoré",
"saint honore" et "SAINT   HONORE" soient reconnus comme identiques.

Sont exclues avant comparaison :
- `OFF/Online = Online`
- `CITY = ONLINE`
- `RETAILER` contenant `retail.com`
- lignes avec `DOOR COUNT` vide ou à 0

### Fichiers générés

- **`new_stores_not_in_bible.csv`** : boutiques scrapées qui ne correspondent
  à aucune porte de la BIBLE (comparaison sur marque + pays + ville + nom de
  porte, normalisés). Uniquement pour les marques dont le scraper renvoie le
  détail par boutique - Diptyque (totaux par pays uniquement, pas de nom de
  porte individuel) n'apparaît jamais ici, seulement dans le fichier de
  différences régionales ci-dessous.
- **`possible_closures.csv`** : portes de la BIBLE non retrouvées dans le
  dernier scrape. **Jamais** marquées comme fermeture confirmée - toujours
  `STATUS = TO VERIFY`, une porte peut manquer d'un relevé sans avoir
  réellement fermé (site changé, page bloquée, filtre FSS trop strict ce
  jour-là). Aucune ligne n'est générée pour une marque quand :
  - le scraper a échoué (`status = error`) ;
  - la marque n'a pas de scraper (`status = manual`) ;
  - la confiance de la marque est `manuelle` ;
  - le scraper a renvoyé un résultat probablement tronqué (`partial`,
    ex. plafond de résultats atteint sur un widget Stockist) ;
  - la couverture scrapée est visiblement incomplète (moins de la moitié du
    nombre de portes que la BIBLE liste pour cette marque).

  Les marques ignorées pour cette raison sont listées en console
  (`(détection de fermeture ignorée pour ... : ...)`) - à traiter comme
  "vérification manuelle nécessaire", pas comme un résultat.
- **`regional_total_differences.csv`** : total de portes BIBLE (`DOOR COUNT`
  sommé) vs total scrapé, par marque et par région - seules les lignes avec
  un écart réel sont listées. Fonctionne aussi pour les marques agrégées
  (Diptyque), puisque cette comparaison ne nécessite que des totaux, pas le
  détail par porte.

Les trois fichiers suivent la même règle que `_a_verifier.csv` : rien à
signaler => le fichier n'est pas (re)créé, pour ne jamais laisser un
résultat d'un run précédent traîner en silence.

## Ajouter une marque

Ajouter un objet dans `brands.yaml` - aucune modification de code requise
pour les cas déjà couverts :

```yaml
- name: "Nom de la marque"
  slug: mon_slug
  store_locator_url: "https://..."
  scraper_type: static_html   # static_html | js_widget | manual
  parser: mfk                 # voir la liste des parsers ci-dessous
  confidence: moyenne         # haute | moyenne | manuelle
  known_total: 20             # optionnel : dernier chiffre connu
  notes: "..."
```

Parsers `static_html` déjà écrits (`scrapers/static.py`) : `diptyque`
(totaux par pays), `mfk`, `nishane`, `caron`. Un nouveau site statique
nécessite une nouvelle fonction `scrape_xxx()` dans ce fichier (regarder la
structure HTML du site à la main, il n'y a pas de parseur générique magique
qui marche partout).

Parsers `js_widget` : `stockist` couvre **tout** widget Stockist (juste
renseigner `stockist_widget_tag`, trouvable dans le HTML de la page via
`data-stockist-widget-tag="..."`) - pas besoin de code par marque. Pour un
widget JS qui n'est pas Stockist, chercher d'abord son appel réseau en
arrière-plan (onglet réseau des devtools) avant de sortir
`scrapers/dynamic.py:scrape_dynamic_playwright()`, qui reste un dernier
recours générique (rendu DOM headless).

`scraper_type: manual` = pas de scraper, `known_total` sert de référence
affichée telle quelle dans le rapport (tag confiance `manuelle`).

## Où sont stockés les identifiants

Dans `.env` (jamais commité, voir `.gitignore`) - copier `.env.example` et
remplir :
- `GMAIL_ADDRESS` / `GMAIL_APP_PASSWORD` : un
  [mot de passe d'application Gmail](https://myaccount.google.com/apppasswords),
  jamais le mot de passe principal du compte.
- `REPORT_RECIPIENT` : à qui envoyer le rapport (généralement soi-même).
- `REGIONAL_TEAM_RECIPIENTS` : liste (séparée par des virgules) pour
  pré-remplir le brouillon d'email régional - jamais utilisée pour un envoi
  automatique.
- `COMPETITION_EXPORT_CSV` : valeur par défaut pour `--existing-file` si
  l'option n'est pas passée en ligne de commande (accepte aussi bien un
  `.xlsx` BIBLE qu'un `.csv` de synthèse, malgré son nom historique).

## Tests

```bash
pip install -r requirements.txt   # inclut pytest
pytest
```

Les tests utilisent un petit onglet `Competition` synthétique généré à la
volée avec `openpyxl` (`tests/test_diff_existing.py`) - ils ne nécessitent
pas le vrai fichier BIBLE et ne touchent à aucun fichier réel.

## Lire le tag de confiance

Chaque ligne du rapport porte un statut et une confiance :

| confiance  | signifie |
|------------|----------|
| `haute`    | scraper statique fiable, filtre FSS propre (ex. Diptyque, Nishane) |
| `moyenne`  | scraper fonctionne mais le filtre mono-marque/wholesale est approximatif (ex. MFK, JHAG, Caron - vérifier `_a_verifier.csv`) |
| `manuelle` | pas de scraper fiable, chiffre de référence à confirmer à la main ou par email régional |

Statut d'exécution (indépendant de la confiance) :
- `OK` : le scraper a tourné et produit un chiffre.
- `ECHEC` : le scraper a planté cette fois-ci (site changé, blocage) - le
  chiffre affiché est celui du dernier relevé réussi si disponible, sinon
  vide. Revérifier l'URL/la structure de la page avant de suspecter le code.
- `MANUEL` : pas de scraper du tout, `known_total` affiché tel quel.

## Limites connues (volontairement pas sur-ingénierées pour l'instant)

- **Résolution pays -> ville** : quand un store locator ne donne pas le pays
  directement (MFK, certains widgets Stockist), le pays est déduit d'une
  petite table ville->pays codée en dur dans `aggregate.py`
  (`CITY_COUNTRY_HINTS`) plutôt qu'un vrai service de géocodage. À
  compléter au fil de l'eau : une ville non reconnue part dans
  `_a_verifier.csv` plutôt que d'être classée au hasard.
- **Couverture mondiale des widgets Stockist** : Stockist n'expose qu'une
  recherche par rayon (pas de "liste tout"), donc `scrapers/dynamic.py`
  interroge un quadrillage d'une quarantaine de grandes métropoles
  (`WORLD_CITY_GRID`) avec un rayon de 250km. Une boutique à plus de 250km
  de tous ces points serait manquée ; une zone très dense (>100 résultats
  dans un rayon) pourrait aussi être tronquée par le plafond `max_results`
  de l'API. Le rapport de delta et `_a_verifier.csv` sont là pour repérer
  ce genre d'écart plutôt qu'une couverture garantie à 100%.
- **Protection anti-bot** : certains sites (MFK notamment, sur Akamai)
  peuvent bloquer des requêtes automatisées après plusieurs appels
  rapprochés, même avec un User-Agent explicite et un délai entre requêtes.
  C'est le cas d'usage exact du statut `ECHEC` - pas la peine de contourner
  la protection, relancer plus tard ou vérifier la marque à la main pour
  cette fois-ci.
- **Créed** : deux sites officiels distincts trouvés
  (creedboutique.com et creedfragrance.com), qui n'ont pas le même
  contenu ni la même fiabilité de filtre FSS - voir la note dans
  `brands.yaml`, marqué `manuel` en attendant un filtre plus fiable.

## Structure du projet

```
brands.yaml                      config (une marque = un objet)
region_mapping.py                pays -> région (EMEA/UK/NOAM/LATAM/CHINA/APAC)
normalize.py                     normalisation texte (accents/casse/ponctuation) pour les comparaisons
known_retailers_blocklist.json   revendeurs multi-marques connus à exclure
scrapers/static.py                scrapers HTML statique (requests + BeautifulSoup)
scrapers/dynamic.py                widget Stockist (API JSON) + Playwright (dernier recours)
aggregate.py                     filtre FSS, région, historique/deltas/tendance, confiance
photos.py                        téléchargement des photos de nouvelles boutiques
diff_existing.py                 recoupement BIBLE .xlsx (porte par porte) + ancien export .csv
draft_regional_email.py          brouillon d'email pour les équipes régionales (jamais envoyé)
report.py                        tableau HTML + export CSV/XLSX
email_sender.py                  envoi Gmail SMTP
run_report.py                    point d'entrée CLI
tests/                           tests automatisés (pytest, onglet Competition synthétique)
conftest.py                      ancre pytest à la racine du projet pour les imports
data/snapshots/                  un relevé daté par run (JSON, gitignoré)
photos/{slug}/                   photos téléchargées / placeholders (gitignoré)
drafts/                           brouillons d'email régional (gitignoré)
_a_verifier.csv                  classifications douteuses du dernier run (gitignoré)
new_stores_not_in_bible.csv      boutiques scrapées absentes de la BIBLE (gitignoré)
possible_closures.csv            portes BIBLE non retrouvées, TO VERIFY (gitignoré)
regional_total_differences.csv  écarts de total par marque/région (gitignoré)
```
