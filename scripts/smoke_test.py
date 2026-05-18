#!/usr/bin/env python3
"""
smoke_test.py
Valida los 3 supuestos críticos del job real ANTES de agregarlo al cron.

Corre desde el servidor con el venv del proyecto:
    /srv/proyectos/video-jhexp/venv/bin/python /srv/proyectos/video-jhexp/scripts/smoke_test.py

Validaciones:
    1. FFmpeg está instalado y es accesible
    2. obtener_precio_yahoo retorna {"precio", "variacion_pct"}
    3. TelegramClient tiene un método send_video(path, caption=...) compatible
       (sin enviar nada todavía — solo introspección)

Si alguna validación falla, imprime exactamente qué hay que ajustar en el job
antes de ponerlo en producción.
"""
from __future__ import annotations

import os
os.environ["CAF_ENV_PATH"] = "/srv/proyectos/video-jhexp/.env"

import sys
import inspect
import shutil
import traceback
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


# Colores para terminal
VERDE = "\033[92m"
ROJO = "\033[91m"
AMARILLO = "\033[93m"
RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"  {VERDE}✓{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"  {ROJO}✗{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"  {AMARILLO}⚠{RESET} {msg}")


def header(titulo: str) -> None:
    print(f"\n{'─' * 60}")
    print(f" {titulo}")
    print(f"{'─' * 60}")


# =============================================================================
# CHECK 1 — FFmpeg
# =============================================================================
def check_ffmpeg() -> bool:
    header("1. FFmpeg instalado y accesible")
    ruta = shutil.which("ffmpeg")
    if not ruta:
        fail("FFmpeg no se encuentra en el PATH")
        print(f"    Solución: sudo dnf install ffmpeg")
        return False
    ok(f"FFmpeg disponible en {ruta}")
    return True


# =============================================================================
# CHECK 2 — Schema de obtener_precio_yahoo
# =============================================================================
def check_yahoo_schema() -> bool:
    header("2. Schema de obtener_precio_yahoo")
    try:
        from caf_tools.api.financial import obtener_precio_yahoo
    except ImportError as e:
        fail(f"No se puede importar caf_tools.api.financial: {e}")
        return False

    try:
        # Usamos un ticker estable que siempre debería responder
        dato = obtener_precio_yahoo("^GSPC")
    except Exception as e:
        fail(f"Llamada a Yahoo falló: {e}")
        return False

    if not isinstance(dato, dict):
        fail(f"Retorno no es dict: tipo={type(dato).__name__}")
        return False

    ok(f"Llamada exitosa, retornó dict con claves: {sorted(dato.keys())}")

    # Las claves que el job espera
    claves_esperadas = {"precio", "variacion_pct"}
    faltantes = claves_esperadas - set(dato.keys())

    if faltantes:
        fail(f"Faltan claves esperadas por el job: {faltantes}")
        print(f"    El job usa: dato['precio'] y dato['variacion_pct']")
        print(f"    Yahoo retornó: {sorted(dato.keys())}")
        print(f"    → Hay que ajustar obtener_datos_mercado() en el job")
        return False

    ok(f"Claves 'precio' y 'variacion_pct' presentes")
    ok(f"Valores: precio={dato['precio']}, variacion_pct={dato['variacion_pct']}")
    return True


# =============================================================================
# CHECK 3 — Firma de TelegramClient.send_video
# =============================================================================
def check_telegram_send_video() -> bool:
    header("3. TelegramClient.send_video (firma compatible)")
    try:
        from caf_tools.api.telegram import TelegramClient
    except ImportError as e:
        fail(f"No se puede importar caf_tools.api.telegram: {e}")
        return False

    # Buscar métodos relacionados con video
    metodos = [m for m in dir(TelegramClient) if not m.startswith("_")]
    metodos_video = [m for m in metodos if "video" in m.lower()]
    metodos_envio = [m for m in metodos if any(k in m.lower() for k in ("send", "enviar", "post"))]

    print(f"    Métodos públicos de TelegramClient: {metodos}")

    if not hasattr(TelegramClient, "send_video"):
        fail("TelegramClient NO tiene método 'send_video'")
        if metodos_video:
            print(f"    Métodos relacionados con video: {metodos_video}")
        if metodos_envio:
            print(f"    Métodos de envío disponibles: {metodos_envio}")
        print(f"    → Ajustar enviar_por_telegram() en el job para usar uno de éstos")
        return False

    ok("Método 'send_video' existe")

    # Verificar firma
    try:
        sig = inspect.signature(TelegramClient.send_video)
        params = list(sig.parameters.keys())
        ok(f"Firma: send_video{sig}")
    except Exception as e:
        warn(f"No se pudo introspeccionar la firma: {e}")
        return True

    # El job llama con: bot.send_video(video_path, caption=caption)
    # → primer parámetro posicional + kwarg 'caption'
    if "caption" not in params:
        fail("La firma no acepta el kwarg 'caption'")
        print(f"    El job lo invoca como: bot.send_video(path, caption=...)")
        print(f"    Parámetros disponibles: {params}")
        print(f"    → Ajustar la llamada en enviar_por_telegram()")
        return False

    ok("Acepta kwarg 'caption' — compatible con el job")
    return True


# =============================================================================
# CHECK 4 (bonus) — Generar un video local sin Telegram
# =============================================================================
def check_engine_funciona() -> bool:
    header("4. video-engine genera un MP4 (test rápido 2s)")
    try:
        from video_engine import VideoConfig
        from video_engine.engine import VideoEngine
        from video_engine.templates import CierreMercadoTemplate
    except ImportError as e:
        fail(f"No se puede importar video_engine: {e}")
        return False

    import tempfile
    output = Path(tempfile.gettempdir()) / "smoke_test_video.mp4"

    config = VideoConfig(
        duracion=2,
        fps=24,
        datos={
            "fecha": "01 / 01 / 2026",
            "merval": {"precio": 1_000_000, "var_pct": 1.5},
            "sp500": {"precio": 5_000, "var_pct": -0.3},
        },
    )

    try:
        engine = VideoEngine(template=CierreMercadoTemplate())
        engine.generar(config, output_path=output)
    except Exception as e:
        fail(f"Falló la generación del video: {e}")
        traceback.print_exc()
        return False

    if not output.exists() or output.stat().st_size < 1000:
        fail(f"Video no se generó correctamente: {output}")
        return False

    ok(f"Video generado: {output} ({output.stat().st_size / 1024:.1f} KB)")
    output.unlink()
    return True


# =============================================================================
# MAIN
# =============================================================================
def main():
    print("\n" + "=" * 60)
    print(" SMOKE TEST — video-jhexp")
    print(" Valida los supuestos del job antes de pasar a producción")
    print("=" * 60)

    resultados = {
        "FFmpeg": check_ffmpeg(),
        "Yahoo schema": check_yahoo_schema(),
        "Telegram send_video": check_telegram_send_video(),
        "Engine funcional": check_engine_funciona(),
    }

    print("\n" + "=" * 60)
    print(" RESUMEN")
    print("=" * 60)
    for nombre, ok_flag in resultados.items():
        marca = f"{VERDE}✓{RESET}" if ok_flag else f"{ROJO}✗{RESET}"
        print(f"  {marca} {nombre}")

    todos_ok = all(resultados.values())
    print()
    if todos_ok:
        print(f"{VERDE} ✓ Todos los checks OK — el job está listo para correr en producción{RESET}")
        sys.exit(0)
    else:
        print(f"{ROJO} ✗ Hay checks que fallaron — ajustar antes de poner el cron{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
