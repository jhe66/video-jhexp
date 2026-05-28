#!/usr/bin/env python3
"""
job_video_cierre_mercado.py
Genera un video de cierre de mercado (Merval + SP500) y lo envía por Telegram
como "bandeja de salida" para que Javier lo descargue y publique manualmente.

Cron: 35 17 * * 1-5   (lun-vie 17:35, 5 minutos después del job de índices LK)

Flujo:
    1. Obtiene Merval y SP500 de Yahoo Finance
    2. Genera el video vertical (1080x1920, 12s) con la plantilla y música de fondo
    3. Guarda el MP4 en /srv/proyectos/video-jhexp/output/YYYY-MM-DD_cierre.mp4
    4. Envía el video por Telegram al chat configurado
    5. Javier lo descarga en el celular y lo publica manualmente en TikTok/Reels
"""
from __future__ import annotations
from video_engine.utils import seleccionar_musica

import os
os.environ["CAF_ENV_PATH"] = "/srv/proyectos/video-jhexp/.env"

import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from caf_tools.api.financial import obtener_cierre_yahoo
from caf_tools.api.telegram import TelegramClient
from caf_tools.utils.helpers import (
    cortar_si_feriado,
    obtener_fecha_hora_argentina,
)
from caf_tools.utils.logger import get_logger

from video_engine import VideoConfig
from video_engine.engine import VideoEngine
from video_engine.templates import CierreMercadoTemplate

logger = get_logger("job_video_cierre_mercado", log_dir="/srv/logs/video-jhexp")

OUTPUT_DIR = Path("/srv/proyectos/video-jhexp/output")


def obtener_datos_mercado() -> dict:
    """Obtiene Merval y SP500 desde Yahoo, devuelve dict listo para el template."""
    logger.info("Obteniendo datos de mercado desde Yahoo Finance...")
    merval = obtener_cierre_yahoo("^MERV")
    sp500 = obtener_cierre_yahoo("^GSPC")

    
    fecha = obtener_fecha_hora_argentina()["fecha_formato"]

    return {
        "fecha": fecha,
        "merval": {
            "precio": merval["precio"],
            "var_pct": merval["variacion_pct"],
        },
        "sp500": {
            "precio": sp500["precio"],
            "var_pct": sp500["variacion_pct"],
        },
    }


def generar_video(datos: dict) -> Path:
    """Genera el video y devuelve el Path al MP4."""
    
    fecha_dict = obtener_fecha_hora_argentina()
    fecha_archivo = f"{fecha_dict['año']}-{fecha_dict['mes']}-{fecha_dict['dia']}" 

    output_path = OUTPUT_DIR / f"{fecha_archivo}_cierre.mp4"

    # Elegir música al azar de /srv/shared/music/ (o None si la biblioteca está vacía)
    musica = seleccionar_musica()
    if musica is None:
        logger.warning("No hay música disponible — el video se generará sin audio")
    else:
        logger.info("Música elegida: %s", musica.name)

    config = VideoConfig(
        duracion=12,
        formato="vertical",
        fps=30,
        paleta="caf_oscuro",
        musica_path=str(musica) if musica else None,
        volumen_musica=0.25,
        datos=datos,
        extras={
            "handle": "@javierexpoar",
            "tagline": "Información financiera diaria",
        },
    )

    engine = VideoEngine(template=CierreMercadoTemplate())
    engine.generar(config, output_path=output_path)
    return output_path


def enviar_por_telegram(video_path: Path, datos: dict) -> None:
    """Envía el video por Telegram con caption informativo."""
    caption = (
        f"🎬 Video cierre de mercado — {datos['fecha']}\n\n"
        f"🇦🇷 Merval: {datos['merval']['precio']:,.0f} "
        f"({datos['merval']['var_pct']:+.2f}%)\n"
        f"🇺🇸 S&P 500: {datos['sp500']['precio']:,.2f} "
        f"({datos['sp500']['var_pct']:+.2f}%)\n\n"
        f"Listo para publicar en TikTok / Reels / Shorts."
    )

    bot = TelegramClient()
    bot.send_video(video_path, caption=caption, parse_mode=None)
    logger.info("Video enviado por Telegram")


def main():
    logger.info("=" * 50)
    logger.info("Iniciando job_video_cierre_mercado")
    cortar_si_feriado()

    try:
        datos = obtener_datos_mercado()
        logger.info(
            "Datos obtenidos — Merval: %s (%+.2f%%), SP500: %s (%+.2f%%)",
            datos["merval"]["precio"], datos["merval"]["var_pct"],
            datos["sp500"]["precio"], datos["sp500"]["var_pct"],
        )

        video_path = generar_video(datos)
        logger.info("Video generado: %s", video_path)

        enviar_por_telegram(video_path, datos)

        logger.info("job_video_cierre_mercado finalizado exitosamente")

    except Exception as e:
        logger.error("Error crítico en job_video_cierre_mercado: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
