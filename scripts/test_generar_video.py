#!/usr/bin/env python3
"""
test_generar_video.py
Test manual para generar un video con datos de prueba (sin llamar a Yahoo ni a Telegram).
Útil para:
- Probar el engine sin depender de servicios externos
- Ver cómo queda el video con datos específicos
- Iterar sobre el look sin esperar al horario de mercado

Uso:
    python scripts/test_generar_video.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from video_engine import VideoConfig
from video_engine.engine import VideoEngine
from video_engine.templates import CierreMercadoTemplate


def main():
    print("\nGenerando video de prueba (sin datos reales)...")

    datos_demo = {
        "fecha": "23 / 04 / 2026",
        "merval": {"precio": 1_847_523, "var_pct": 2.34},
        "sp500":  {"precio": 5_812.45,  "var_pct": -0.42},
    }

    config = VideoConfig(
        duracion=12,
        formato="vertical",
        fps=30,
        paleta="caf_oscuro",
        datos=datos_demo,
    )

    output_path = Path(__file__).parent.parent / "output" / "test_cierre.mp4"

    engine = VideoEngine(template=CierreMercadoTemplate())
    engine.generar(config, output_path=output_path)

    print(f"\n✓ Video generado: {output_path}")
    print(f"  Podés visualizarlo con: vlc {output_path}")


if __name__ == "__main__":
    main()
