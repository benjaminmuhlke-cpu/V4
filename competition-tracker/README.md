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
4. Recoupe avec l'export CSV existant de l'onglet Competition de la BIBLE
   (si `COMPETITION_EXPORT_CSV` est renseigné dans `.env`) et ne remonte que
   les écarts significatifs.
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
   et le script le signale clairement au lieu d'échouer.

Un scraper qui échoue (site changé, blocage anti-bot) n'interrompt jamais
le reste du run : la marque apparaît en `[ECHEC]` dans le rapport avec le
message d'erreur, plutôt qu'un chiffre à zéro silencieux.

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
- `COMPETITION_EXPORT_CSV` : chemin vers un export CSV de l'onglet
  Competition de la BIBLE, pour ne remonter que les écarts.

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
known_retailers_blocklist.json   revendeurs multi-marques connus à exclure
scrapers/static.py                scrapers HTML statique (requests + BeautifulSoup)
scrapers/dynamic.py                widget Stockist (API JSON) + Playwright (dernier recours)
aggregate.py                     filtre FSS, région, historique/deltas/tendance, confiance
photos.py                        téléchargement des photos de nouvelles boutiques
diff_existing.py                 recoupement avec l'export CSV Competition existant
draft_regional_email.py          brouillon d'email pour les équipes régionales (jamais envoyé)
report.py                        tableau HTML + export CSV/XLSX
email_sender.py                  envoi Gmail SMTP
run_report.py                    point d'entrée CLI
data/snapshots/                  un relevé daté par run (JSON, gitignoré)
photos/{slug}/                   photos téléchargées / placeholders (gitigноré)
drafts/                           brouillons d'email régional (gitignoré)
_a_verifier.csv                  classifications douteuses du dernier run (gitignoré)
```
