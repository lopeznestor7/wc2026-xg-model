#!/usr/bin/env bash
# ==============================================================================
#  Inicializa el repositorio y lo sube a GitHub.
#
#  Requisito previo: crea un repositorio VACÍO en GitHub (sin README ni licencia,
#  para evitar conflictos) desde https://github.com/new. Nombre sugerido:
#      wc2026-xg-model
#
#  Luego ejecuta este script desde la raíz del proyecto:
#      bash subir_a_github.sh
# ==============================================================================
set -e

USUARIO="lopeznestor7"
REPO="wc2026-xg-model"

# 1. Inicializar git (si no existe ya)
if [ ! -d .git ]; then
    git init
    git branch -M main
fi

# 2. Configurar identidad si no está (ajusta a tu correo de GitHub)
git config user.name  >/dev/null 2>&1 || git config user.name  "Nestor Lopez"
git config user.email >/dev/null 2>&1 || git config user.email "lopez.nestor@pucp.edu.pe"

# 3. Añadir todo (el .gitignore excluye cache, venv, temporales de LaTeX)
git add .
git commit -m "Modelo de expected goals con ajuste por rival — Final Mundial 2026"

# 4. Conectar con el remoto y subir
git remote add origin "https://github.com/${USUARIO}/${REPO}.git" 2>/dev/null || \
    git remote set-url origin "https://github.com/${USUARIO}/${REPO}.git"

git push -u origin main

echo ""
echo ">>> Listo. Repositorio en: https://github.com/${USUARIO}/${REPO}"
