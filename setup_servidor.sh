#!/bin/bash
# =============================================================================
# setup_servidor.sh — video-jhexp
# Ejecutar en el servidor como root o con sudo
# =============================================================================

set -e

PROJECT="video-jhexp"
PROJECT_DIR="/srv/proyectos/$PROJECT"
LOG_DIR="/srv/logs/$PROJECT"

echo ""
echo "============================================="
echo " Configurando $PROJECT en el servidor"
echo "============================================="

# 1. Verificar que FFmpeg está instalado (requisito del video-engine)
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg no está instalado."
    echo "   Instalar con: sudo dnf install ffmpeg"
    exit 1
fi
echo "✓ FFmpeg disponible: $(ffmpeg -version | head -1)"

# 2. Verificar que existe video-engine en /srv/shared
if [ ! -d "/srv/shared/video-engine" ]; then
    echo "❌ No se encuentra /srv/shared/video-engine"
    echo "   Cloná primero el repo de video-engine:"
    echo "   sudo git clone git@github.com:jhe66/video-engine.git /srv/shared/video-engine"
    exit 1
fi
echo "✓ /srv/shared/video-engine encontrado"

# 3. Directorios
echo "📁 Creando directorios..."
sudo mkdir -p "$PROJECT_DIR/jobs"
sudo mkdir -p "$PROJECT_DIR/output"
sudo mkdir -p "$LOG_DIR"

# 4. Permisos
echo "🔒 Configurando permisos..."
sudo chown -R caf:cafdev "$PROJECT_DIR"
sudo chown -R caf:cafdev "$LOG_DIR"
sudo chmod -R 775 "$PROJECT_DIR"
sudo chmod -R 775 "$LOG_DIR"
sudo find "$PROJECT_DIR" -type d -exec chmod g+s {} \;

# 5. Entorno virtual Python 3.11
echo "🐍 Creando venv con Python 3.11..."
cd "$PROJECT_DIR"
python3.11 -m venv venv
venv/bin/pip install --upgrade pip setuptools

# 6. Instalar librerías compartidas
echo "📦 Instalando video-engine y caf-tools..."
venv/bin/pip install -e /srv/shared/video-engine
venv/bin/pip install -e /srv/shared/caf-tools

# 7. Dependencias adicionales para tests
venv/bin/pip install pytest

# 8. .env
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "🔑 Creando .env..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    chmod 640 "$PROJECT_DIR/.env"
    chown admin:cafdev "$PROJECT_DIR/.env"
    echo "   ⚠️  Completá las credenciales en $PROJECT_DIR/.env"
else
    echo "ℹ️  .env ya existe, no se sobreescribió"
fi

# 9. Git safe.directory
git config --global --add safe.directory "$PROJECT_DIR"

echo ""
echo "============================================="
echo " ✅ Setup completado"
echo "============================================="
echo ""
echo " Próximos pasos:"
echo "   1. Completar credenciales: nano $PROJECT_DIR/.env"
echo "   2. Test de engine:         venv/bin/python scripts/test_generar_video.py"
echo "   3. Correr tests:           venv/bin/python -m pytest tests/"
echo "   4. Job real (manual):      venv/bin/python jobs/job_video_cierre_mercado.py"
echo "   5. Agregar al crontab:     sudo crontab -u caf -e"
echo ""
