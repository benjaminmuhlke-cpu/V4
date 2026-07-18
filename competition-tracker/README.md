# Veille concurrentielle FSS/FSF

Outil personnel pour repérer les **ouvertures récentes** de boutiques en
propre (FSS/FSF - Free Standing Store/Flagship, **pas** les corners
multi-marques ni les distributeurs wholesale) chez les marques de
parfumerie de niche concurrentes, et les recouper avec la BIBLE existante
avant de les y ajouter.

Esprit du projet : le plus simple qui marche. Stdlib d'abord, un fichier de
config (`brands.yaml`), pas de base de données, pas d'abstraction au-delà
de ce qui est réellement utilisé.

## Installer

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`playwright` est dans `requirements.txt` mais n'est utilisé que si une
future marque `js_widget` n'expose aucune API JSON (dernier recours). Il
n'est pas nécessaire pour les marques actuellement dans `brands.yaml`.

## 1. Workflow normal : ouvertures récentes

C'est le **seul workflow par défaut**. Il ne fait qu'une chose : repérer
les ouvertures FSS/FSF récentes et confirmées, absentes de la BIBLE, et les
mettre dans un classeur Excel à trois onglets prêt à relire.

```bash
python run_report.py \
  --brands pdm,amouage,creed,matiere_premiere,mfk,byredo,nishane,ex_nihilo,bdk,initio \
  --existing-file "./BIBLE KP & FM Distribution List.xlsx" \
  --recent-days 60 \
  --output "./recent_openings.xlsx" \
  --no-email
```

(`--brands` a cette liste comme valeur par défaut - inutile de la retaper
pour un run complet. `--no-email` est accepté mais n'a aucun effet : ce
workflow n'envoie jamais d'email, voir "Modules legacy" plus bas.)

Chaque exécution :
1. Scrape les store locators (`brands.yaml`) des marques demandées
   (`aggregate.py`). Pour Parfums de Marly, Amouage, Creed et Juliette Has
   A Gun, le filtrage FSS/FSF vs wholesale/grand magasin/parfumerie passe
   par un jeu de règles dédié par marque (`fss_classifier.py` +
   `fss_classification_rules.yaml`), construit à partir de vraies données
   scrapées après que le filtre générique se soit révélé massivement
   pollué par des revendeurs pour ces marques à forte distribution
   wholesale. Les autres marques utilisent le filtre générique
   (mot-clé + `known_retailers_blocklist.json`).
2. Charge la BIBLE (`.xlsx`, onglet `Competition`, **lecture seule -
   jamais modifiée**) et le cache de recherche en ligne curatée
   (`data/online_research_cache.json` - voir sa docstring dans
   `online_research.py` pour pourquoi c'est un cache et pas une recherche
   live).
3. Pour chaque ouverture candidate, deux voies de découverte indépendantes
   (ni l'une ni l'autre n'est un prérequis pour l'autre - voir
   `recent_openings.py`) :
   - **A.** une boutique retrouvée par le scraper, recoupée avec une preuve
     d'ouverture datée dans le cache ;
   - **B.** une annonce d'ouverture datée dans le cache, vérifiée contre le
     store locator officiel et la BIBLE - même si le scraper ne l'a jamais
     retrouvée lui-même (liste figée, pagination, blocage, ou juste un nom
     de porte orthographié différemment).
4. Classe chaque candidat :
   - **date connue, dans la fenêtre `--recent-days`, absente de la BIBLE**
     -> `RECENT OPENINGS`.
   - **date connue, hors fenêtre** -> exclue (ce n'est plus "récent" ; ce
     n'est pas non plus une question ouverte, donc jamais dans `TO VERIFY`).
   - **déjà présente dans la BIBLE** (y compris sous un nom/orthographe
     différent entre le scraper, le cache et la BIBLE) -> exclue.
   - **date inconnue, mais candidat FSS/FSF plausible et absent de la
     BIBLE** -> `TO VERIFY`.
   - **développement retail réel mais non-FSS/FSF** (boutique travel-retail,
     ouverture en grand magasin, corner/concession, shop-in-shop, pop-up,
     relocalisation, réouverture, ou un développement non-FSS resté flou)
     -> `OTHER OPENINGS`, jamais mélangé aux vraies ouvertures FSS/FSF.
   - **pas l'initiative de la marque du tout** (parfumerie indépendante,
     revendeur multi-marques, vente en ligne) -> exclue entièrement.
5. Écrit le classeur (`--output`, par défaut `recent_openings.xlsx`) à
   **trois onglets** :
   - **`RECENT OPENINGS`** : ouvertures FSS/FSF confirmées à ajouter à la
     BIBLE (avec `SECOND SOURCE`/`SECOND SOURCE URL` quand une deuxième
     source indépendante corrobore la même porte).
   - **`TO VERIFY`** : candidats FSS/FSF plausibles mais non tranchés (date
     d'ouverture inconnue, ou source LinkedIn sans annonce d'origine
     identifiée - voir `_is_unattributed_linkedin_repost`).
   - **`OTHER OPENINGS`** : développements retail réels mais non-FSS/FSF
     (travel-retail, grand magasin, corner/concession, shop-in-shop,
     pop-up, relocalisation, réouverture) - à titre d'information, jamais
     ajoutés à la BIBLE.
   - les trois : en-tête figé, filtres automatiques, colonnes
     dimensionnées, liens `SOURCE URL`/`SECOND SOURCE URL` cliquables.
6. Affiche en console un résumé (marques vérifiées, lignes par onglet,
   exclusions par catégorie).

Un scraper qui échoue n'interrompt jamais le reste du run - la marque
retombe sur le dernier relevé du jour (`data/snapshots/`) ou sur ce que le
cache de recherche sait d'elle, plutôt qu'un chiffre à zéro silencieux.

## 2. Diagnostic optionnel du classifieur FSS/FSF

Pour les marques qui ont un jeu de règles dédié dans
`fss_classification_rules.yaml` (Parfums de Marly, Amouage, Creed,
Juliette Has A Gun), `--include-classifier-diagnostics` génère en plus deux
fichiers pour évaluer la qualité de ce filtre :

```bash
python run_report.py \
  --brands pdm,amouage,creed,jhag \
  --existing-file "./BIBLE KP & FM Distribution List.xlsx" \
  --recent-days 60 \
  --output "./recent_openings.xlsx" \
  --include-classifier-diagnostics \
  --no-email
```

- **`data/fss_filter_quality.csv`** : par marque, nombre de boutiques
  brutes/incluses/exclues par catégorie, écart vs le total FSS/FSF de la
  BIBLE, et un statut (`RELIABLE` / `NEEDS_REVIEW` / `UNRELIABLE` /
  `INSUFFICIENT_DATA`) - voir `fss_filter_quality.py`. Ne peut **jamais**
  être `RELIABLE` tant qu'un humain n'a pas rempli `MANUAL_VERDICT` dans le
  fichier suivant.
- **`data/fss_validation_sample.csv`** : un échantillon manuellement
  vérifiable (boutiques incluses, exclues, ambiguës, toutes régions
  représentées) avec des colonnes `MANUAL_VERDICT` / `MANUAL_NOTES` à
  remplir à la main ; relancer avec ce flag relit un fichier déjà rempli
  pour affiner le statut du filtre au fil des relances.

Ce flag est **sans effet sur `recent_openings.xlsx`** : le diagnostic lit
les données déjà calculées par le scraper (`aggregate.py`), il ne modifie
rien dans le pipeline d'ouvertures récentes. Absent du flag, aucun des deux
fichiers n'est (re)généré.

## 3. Sources complémentaires et univers concurrentiel élargi

`news_sources.yaml` documente 15 sources presse/LinkedIn curatées
(FashionNetwork, The Moodie Davitt Report, TRBusiness, Business of Fashion,
Vogue Business, Cosmetics Business...) qui **complètent, sans jamais
remplacer**, les sources officielles (site/newsroom/LinkedIn de la marque,
mall/landlord officiel) - voir l'en-tête du fichier pour le barème de
priorité à 3 niveaux. Ce fichier est une référence pour alimenter
`data/online_research_cache.json` à la main (ou via une session Claude Code
avec accès recherche web, hors de ce script - voir la docstring
d'`online_research.py`) ; rien ici n'exécute de recherche live.

`brands.yaml` suit désormais 22 marques (les 10 du run par défaut plus
Diptyque, Maison Margiela, L'Artisan Parfumeur, Penhaligon's, Caron, Serge
Lutens, Maison Crivelli, Goutal, Memo Paris, Kayali, Floraïku Paris...) et
`premium_mainstream_collections.yaml` prépare le suivi de lignes de parfum
"niche" appartenant à des groupes mainstream, volontairement laissé vide
tant qu'aucune ligne n'est confirmée (voir son en-tête pour le schéma).

Trois options CLI supplémentaires, toutes désactivées par défaut pour que
le run standard reste conservateur :

```bash
python run_report.py \
  --all-tracked-brands \
  --existing-file "./BIBLE KP & FM Distribution List.xlsx" \
  --recent-days 60 \
  --include-industry-news \
  --include-travel-retail \
  --output "./recent_openings.xlsx" \
  --no-email
```

- **`--all-tracked-brands`** : vérifie les 22 marques de `brands.yaml` au
  lieu de la liste `--brands` (qui est alors ignorée).
- **`--include-industry-news`** : prend en compte les entrées du cache dont
  la source vient d'un des 15 titres de `news_sources.yaml` - absent par
  défaut, ces entrées sont simplement ignorées (comptées dans "Curated
  industry-news findings skipped" en console) pour ne jamais gonfler le
  résultat standard de candidats presse non essentiels.
- **`--include-travel-retail`** : prend en compte les découvertes
  classées `TRAVEL_RETAIL_BOUTIQUE` (aéroport/duty-free) dans
  `OTHER OPENINGS` - jamais dans `RECENT OPENINGS`, quel que soit ce flag.
- **`--source-refresh`** : vide les entrées du cache pour les marques de ce
  run avant de le lancer (même logique que l'ancien
  `--refresh-online-research` - ce script ne peut pas lancer de recherche
  live lui-même, ça ne fait que préparer le cache à être réalimenté).

Un post LinkedIn n'est promu en `RECENT OPENINGS` que s'il n'est pas un
simple repost non attribué : une entrée `source_type: linkedin_post` sans
`original_source_url` retombe toujours en `TO VERIFY`, même datée et
`CONFIRMED` (le compte officiel de la marque/du mall utilise plutôt
`official_verified_brand_social_post`, toujours de confiance).

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
(totaux par pays), `mfk`, `nishane`, `caron`. Parsers `js_widget` :
`stockist` couvre tout widget Stockist (renseigner
`stockist_widget_tag`) - pas besoin de code par marque.

Pour donner à une nouvelle marque son propre filtre FSS/FSF déterministe
(plutôt que le filtre générique par mot-clé), ajouter une section dans
`fss_classification_rules.yaml` (voir son en-tête pour le schéma exact et
l'ordre de priorité des règles) - `fss_classifier.py` n'a besoin d'aucune
modification, il lit uniquement ce YAML.

## Tests

```bash
pip install -r requirements.txt   # inclut pytest
pytest
```

Les tests utilisent des fixtures synthétiques (`openpyxl`, cache de
recherche factice) - ils ne nécessitent pas le vrai fichier BIBLE et ne
touchent à aucun fichier réel.

## Modules legacy intentionnellement inutilisés

Ces fichiers existent encore dans le dépôt (tests inclus, tous verts) mais
**ne sont plus appelés par `run_report.py`** depuis le passage au workflow
"ouvertures récentes" ci-dessus. Ils ne doivent **pas** être reconnectés
sans une décision explicite : pas de retour du traitement PDF, de l'email,
des photos, du suivi de fermetures, des analyses historiques/tendance, ni
des rapports d'audit larges.

| Fichier | Rôle (désormais inactif) |
|---|---|
| `pdf_reference.py` | extraction du PDF "Competition Distribution" |
| `three_source_comparison.py` | comparaison website vs BIBLE vs PDF |
| `photos.py` | téléchargement de photos de nouvelles boutiques |
| `email_sender.py` | envoi du rapport par Gmail SMTP |
| `draft_regional_email.py` | brouillon d'email pour les équipes régionales |
| `report.py` | ancien rapport HTML + export CSV/XLSX régional |
| `coverage_audit.py` | audit large de couverture par marque (`brand_coverage_audit.csv`, `manual_follow_up.csv`) |

Note sur `coverage_audit.py` : il reste **importé** (pas orphelin au sens
strict) car `online_research.py` utilise sa fonction
`needs_manual_follow_up()` pour savoir quelles marques ont du contenu dans
le cache de recherche. Seule sa propre fonction de génération de rapport
(`build_coverage_audit()` et les CSV associés) n'est plus appelée par
personne.

`diff_existing.py` n'est **pas** dans cette liste : sa lecture de la BIBLE
(`load_bible_competition`, `build_bible_index`, `filter_bible_rows`) et son
utilitaire d'écriture CSV (`write_rows_csv`) sont toujours au cœur du
workflow actif ; seules ses fonctions de suivi de fermetures/nouvelles
boutiques/écarts régionaux (`find_possible_closures`,
`find_new_stores`, `find_regional_total_differences`) ne sont plus
appelées par `run_report.py`.

## Limites connues (volontairement pas sur-ingénierées pour l'instant)

- **Résolution pays -> ville** : quand un store locator ne donne pas le pays
  directement, le pays est déduit d'une petite table ville->pays codée en
  dur dans `aggregate.py` (`CITY_COUNTRY_HINTS`) plutôt qu'un vrai service
  de géocodage.
- **Couverture mondiale des widgets Stockist** : Stockist n'expose qu'une
  recherche par rayon, donc `scrapers/dynamic.py` interroge un
  quadrillage d'une quarantaine de grandes métropoles (`WORLD_CITY_GRID`,
  rayon 250km) - une boutique très isolée pourrait être manquée, une zone
  très dense pourrait être tronquée par le plafond de résultats de l'API.
- **Protection anti-bot** : certains sites peuvent bloquer des requêtes
  automatisées après plusieurs appels rapprochés - pas la peine de
  contourner la protection, relancer plus tard.
- **Rapprochement de noms entre sources** : le scraper, le cache de
  recherche et la BIBLE n'orthographient pas toujours une même porte à
  l'identique (ex. "Boutique Marais" vs "LE MARAIS") - `recent_openings.py`
  vérifie chaque nom disponible (scraper *et* entrée de recherche) contre
  la BIBLE avant de conclure qu'une porte est nouvelle, mais un
  rapprochement plus flou (jamais tenté ici) resterait possible à affiner.

## Structure du projet

```
brands.yaml                          config (une marque = un objet, 22 marques suivies)
news_sources.yaml + .py              sources presse/LinkedIn curatées complémentaires
premium_mainstream_collections.yaml  lignes de parfum niche de groupes mainstream (vide, à alimenter)
region_mapping.py                    pays -> région (EMEA/UK/NOAM/LATAM/CHINA/APAC)
normalize.py                         normalisation texte (accents/casse/ponctuation)
brand_aliases.json + .py             alias de marque entre sources
known_retailers_blocklist.json       revendeurs multi-marques connus à exclure (filtre générique)
fss_classification_rules.yaml        règles FSS/FSF dédiées par marque (PDM, Amouage, Creed, JHAG)
fss_classifier.py                    applique fss_classification_rules.yaml
fss_filter_quality.py                diagnostic optionnel de qualité du filtre FSS/FSF
scrapers/static.py                   scrapers HTML statique (requests + BeautifulSoup)
scrapers/dynamic.py                  widget Stockist (API JSON) + Playwright (dernier recours)
aggregate.py                         scrape + filtre FSS + région, par marque
diff_existing.py                     lecture BIBLE .xlsx (onglet Competition, lecture seule)
online_research.py                   cache de recherche en ligne curatée (data/online_research_cache.json)
recent_openings.py                   pipeline ouvertures récentes (RECENT OPENINGS/TO VERIFY/OTHER OPENINGS) + classeur Excel
run_report.py                        point d'entrée CLI
tests/                               tests automatisés (pytest, fixtures synthétiques)
conftest.py                          ancre pytest à la racine du projet pour les imports
data/snapshots/                      un relevé daté par run (JSON, gitignoré)
data/online_research_cache.json      cache de recherche curatée (commité, pas gitignoré)
data/fss_filter_quality.csv          diagnostic optionnel (gitignoré, --include-classifier-diagnostics)
data/fss_validation_sample.csv       diagnostic optionnel (gitignoré, --include-classifier-diagnostics)
recent_openings.xlsx                 classeur de sortie (gitignoré)

pdf_reference.py, three_source_comparison.py, photos.py, email_sender.py,
draft_regional_email.py, report.py, coverage_audit.py   modules legacy - voir
                                                          section dédiée ci-dessus
```
