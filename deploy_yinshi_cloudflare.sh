#!/usr/bin/env bash
set -euo pipefail

# Déploiement de la documentation Yinshi vers Cloudflare Pages
# 1) Build MkDocs en local
# 2) Déploiement du dossier ./site via wrangler

# Répertoire racine du projet md2html
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "[deploy] Répertoire courant : $ROOT_DIR"

# Activer le venv si présent
if [ -d ".venv" ]; then
  echo "[deploy] Activation du venv .venv"
  # shellcheck disable=SC1091
  source .venv/bin/activate
else
  echo "[deploy] Attention : aucun venv .venv trouvé, mkdocs utilisera l'environnement global"
fi

# Build MkDocs (lit ../yinshi/docs via mkdocs.yml)
echo "[deploy] Build MkDocs..."
mkdocs build --clean

echo "[deploy] Build terminé, déploiement vers Cloudflare Pages..."

# Nom du projet Cloudflare Pages à créer côté dashboard
PROJECT_NAME="yinshi-docs"

# Déploie le contenu du dossier ./site vers le projet Cloudflare Pages
wrangler pages deploy "site" --project-name="$PROJECT_NAME"

echo "[deploy] Terminé. Vérifie le déploiement dans le dashboard Cloudflare Pages (projet: $PROJECT_NAME)."
