# video-jhexp — Generador de videos para publicación manual

## Descripción
Genera videos cortos (tarjetas animadas) de contenido financiero y los envía por
Telegram como "bandeja de salida". Javier los descarga en el celular y los
publica manualmente en TikTok, Reels, Shorts o LinkedIn.

## Stack
- Python 3.11
- video-engine (librería compartida, en `/srv/shared/video-engine`)
- caf-tools (librería compartida, en `/srv/shared/caf-tools`)
- FFmpeg (renderizado)
- Rocky Linux + Cron (usuario `caf`)

---

## Estructura
```
video-jhexp/
├── jobs/
│   └── job_video_cierre_mercado.py   ← genera video cierre Merval + SP500
├── scripts/
│   └── test_generar_video.py         ← test manual sin datos reales
├── tests/
│   └── test_video_engine.py          ← tests unitarios
├── output/                           ← MP4 generados (NO subir a git)
├── .env.example
├── requirements.txt
└── setup_servidor.sh
```

---

## Flujo operativo

```
Cron (17:35)
    ↓
Job obtiene Merval + SP500 de Yahoo Finance
    ↓
video-engine renderiza MP4 vertical 12s
    ↓
Se guarda en /srv/proyectos/video-jhexp/output/
    ↓
Se envía por Telegram al chat de Javier
    ↓
Javier lo descarga en el celular
    ↓
Publica manualmente en TikTok / Reels / Shorts / LinkedIn
```

## Setup inicial

```bash
# 1. Clonar el repo
sudo git clone git@github.com:jhe66/video-jhexp.git /srv/proyectos/video-jhexp

# 2. Correr setup del servidor
cd /srv/proyectos/video-jhexp
sudo bash setup_servidor.sh

# 3. Completar credenciales (ya debería copiarse desde caf-tools)
nano /srv/proyectos/video-jhexp/.env

# 4. Verificar que FFmpeg está instalado
ffmpeg -version

# 5. Generar un video de prueba (sin datos reales)
venv/bin/python scripts/test_generar_video.py

# 6. Correr el job real
venv/bin/python jobs/job_video_cierre_mercado.py

# 7. Correr tests
venv/bin/python -m pytest tests/
```

## Comandos
```bash
# Test rápido (sin llamar a Yahoo ni Telegram)
venv/bin/python scripts/test_generar_video.py

# Job real (requiere datos de mercado y Telegram configurado)
venv/bin/python jobs/job_video_cierre_mercado.py

# Tests
venv/bin/python -m pytest tests/ -v
```

## Crontab (usuario caf)
```bash
PYTHON=/srv/proyectos/video-jhexp/venv/bin/python
PROJECT=/srv/proyectos/video-jhexp
LOGS=/srv/logs/video-jhexp

# Video cierre de mercado — lun-vie 17:35 (5 min después del job LK de índices)
35 17 * * 1-5  $PYTHON $PROJECT/jobs/job_video_cierre_mercado.py >> $LOGS/job_video_cierre_mercado.log 2>&1
```

## Variables de entorno (.env)
Las hereda de caf-tools:
```bash
DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
```

Usa las mismas credenciales que los otros proyectos del stack.

## Reglas importantes
- Siempre definir `CAF_ENV_PATH` antes de importar `caf_tools`
- Usar `cortar_si_feriado()` en jobs lun-vie
- Los videos en `output/` NO se suben a git
- Logs en `/srv/logs/video-jhexp/`
- Las pruebas de integración demoran ~5s (renderizan un video de 2s)

## Parametrización del engine

El engine es totalmente parametrizable. Para cambiar duración, formato o paleta,
editar el `VideoConfig` en el job correspondiente:

```python
config = VideoConfig(
    duracion=8,              # 5-60s
    formato="cuadrado",      # vertical | cuadrado | horizontal
    fps=30,                  # 24, 30 o 60
    paleta="minimal_negro",  # caf_oscuro | minimal_negro | claro_premium
    ...
)
```

Sin tocar el engine. Mañana querés probar un video horizontal para LinkedIn →
copiás el job, cambiás 2 parámetros, listo.

## Roadmap

**Fase 1 — MVP (actual)**
- ✅ Plantilla cierre_mercado vertical 12s
- ✅ Engine configurable
- ✅ Tests
- ✅ Bandeja por Telegram

**Fase 2 — Más plantillas**
- ⏳ Frase célebre (reutiliza DB de caf-tools)
- ⏳ ETF/CEDEAR spotlight aleatorio
- ⏳ Efemérides financieras

**Fase 3 — Multi-formato**
- ⏳ Soportar formato cuadrado y horizontal en las plantillas existentes
- ⏳ Una sola config → export en los 3 formatos de una

**Fase 4 — Música**
- ⏳ Biblioteca de música libre de derechos
- ⏳ Mood musical por tipo de video

**Fase 5 — HTML/CSS**
- ⏳ Evaluar migración de capa de plantillas a HTML + Playwright
- ⏳ Permite diseñar en Figma y exportar a HTML

## Convenciones Git
```bash
git commit -m "tipo(scope): descripción"
# feat, fix, refactor, docs, test, chore
```
