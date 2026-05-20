# md2html

Ce dépôt contient une configuration **MkDocs + Material** permettant de **générer un site HTML statique** à partir de documentation Markdown.

L'objectif est de pouvoir :

- Construire/servir la doc en local sans modifier le dépôt source.
- Déployer la doc (ex: Cloudflare Pages) sous forme de site statique.

> Important : ce projet ne "convertit" pas du Markdown arbitraire en HTML.
> Il encapsule principalement MkDocs (et quelques surcharges) pour construire la documentation.

## Multi-Projet

Ce dépôt supporte plusieurs projets via des fichiers de configuration séparés :

- `mkdocs.yinshi.yml` : Configuration pour le projet Yinshi
- `mkdocs.bazi.yml` : Configuration pour le projet Ba Zi

Pour ajouter un nouveau projet, créez un fichier `mkdocs.<projet>.yml` avec la configuration appropriée.

## Pré-requis

- Python 3.x
- (Optionnel) Node.js + `wrangler` si tu veux déployer sur Cloudflare Pages
- Les dépôts source doivent être accessibles depuis les chemins configurés dans les fichiers `mkdocs.*.yml`

## Installation (local)

Recommandé : créer un venv.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install mkdocs mkdocs-material pymdown-extensions
```

## Usage

### Serve (dev)

```bash
# Yinshi
mkdocs serve -f mkdocs.yinshi.yml

# Ba Zi
mkdocs serve -f mkdocs.bazi.yml
```

Puis ouvrir l'URL affichée par MkDocs (souvent `http://127.0.0.1:8000`).

### Build (HTML statique)

```bash
# Yinshi
mkdocs build --clean -f mkdocs.yinshi.yml

# Ba Zi
mkdocs build --clean -f mkdocs.bazi.yml
```

Le site est généré dans le dossier `site/` (ignoré par Git via `.gitignore`).

## Déploiement Cloudflare Pages

Les scripts de déploiement sont temporaires et seront déplacés dans les projets respectifs quand md2html deviendra un paquet Python installable.

### Yinshi

Le script `deploy_yinshi.sh` fait :

- Activation du venv `.venv` si présent
- `mkdocs build --clean -f mkdocs.yinshi.yml`
- `wrangler pages deploy site --project-name="yinshi-docs"`

Exécution :

```bash
./deploy_yinshi.sh
```

### Ba Zi

Le script `deploy_bazi.sh` fait :

- Activation du venv `.venv` si présent
- `mkdocs build --clean -f mkdocs.bazi.yml`
- `wrangler pages deploy site --project-name="bazi-docs"`

Exécution :

```bash
./deploy_bazi.sh
```

Pré-requis pour les deux scripts :

- `wrangler` installé et authentifié
- Les projets Cloudflare Pages (`yinshi-docs`, `bazi-docs`) créés côté dashboard

## Ce que contient le projet (architecture)

- `mkdocs.yinshi.yml` / `mkdocs.bazi.yml`
  - Configuration MkDocs par projet
  - `docs_dir` : chemin vers la documentation du projet
  - Pas de section `nav` : la navigation est générée automatiquement depuis l'arborescence
  - Extensions Markdown : `admonition`, `pymdownx.snippets`, `pymdownx.superfences` (dont fence `mermaid`)
- `hooks.py`
  - Hook `on_nav` : calcule les **dernières mises à jour** (via `git log` si possible, sinon `mtime`) et les expose dans `config.extra.recent_updates`
  - Hook `on_page_markdown` : pour `index.md`, force l'utilisation du template `home.html`
- `overrides/home.html`
  - Injecte un bloc "Dernières mises à jour" sur la page d'accueil (si disponible)
- `overrides/partials/nav-item.html`
  - Surcharge du rendu de la navigation Material
  - Affiche le **nom de fichier** quand possible
  - Affiche le **nom du dossier** à la place de `README.md` (ergonomie navigation)

## Capacités

- Génération d'un site statique HTML à partir de documentation Markdown (multi-projet)
- Navigation auto basée sur l'arborescence (pas de `nav:` à maintenir)
- Bloc "Dernières mises à jour" sur la home (basé sur Git si disponible)
- Support fences `mermaid` (via `pymdownx.superfences`)

## Limitations / Hypothèses

- Les chemins `docs_dir` doivent être configurés correctement dans chaque fichier `mkdocs.*.yml`.
- Dépend de `git` pour enrichir "Dernières mises à jour" (sinon fallback `mtime`).
- Ce dépôt est une **configuration de site** MkDocs, pas une librairie packagée (pas de `pyproject.toml`).
- Les scripts de déploiement sont temporaires et seront déplacés dans les projets respectifs.

## Pistes d'évolution (future "librairie")

L'objectif à moyen terme est de transformer ce dépôt en un paquet Python installable dans n'importe quel projet.

1. **Packaging Python** (objectif à moyen terme)
   - Transformer ce dépôt en package `md2html`
   - Fournir une CLI stable :
     - `md2html serve --config mkdocs.yml`
     - `md2html build --config mkdocs.yml`
   - Garder `hooks.py` et `overrides/` comme "assets" du package
   - Les scripts de déploiement seront gérés par les projets ou CI/CD

2. **Intégration CI/CD** (recommandé pour l'automatisation)
   - Utiliser GitHub Actions ou GitLab CI dans chaque projet
   - Le paquet md2html ne gère que le build/serve
   - Le déploiement reste la responsabilité du projet ou de l'infrastructure

Quand tu veux, on peut décider ensemble :

- Le contrat d'entrée (un dossier docs ? un repo ? une config MkDocs ?)
- Le contrat de sortie (dossier `site/` ? zip ? upload ?)
- Si on vise une intégration **dev only** (documentation) ou une intégration **runtime** (génération à la volée)
