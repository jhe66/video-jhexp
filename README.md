# video-jhexp

Generador de videos para redes sociales — publicación manual via Telegram.

## Setup rápido

```bash
# 1. Setup servidor
sudo bash setup_servidor.sh

# 2. Completar .env
nano /srv/proyectos/video-jhexp/.env

# 3. Test sin dependencias externas
venv/bin/python scripts/test_generar_video.py

# 4. Job real
venv/bin/python jobs/job_video_cierre_mercado.py
```

Ver `CLAUDE.md` para documentación completa.
