"""
Tests básicos del video-engine y la plantilla cierre_mercado.
Corren rápido (~5s) porque renderizan pocos frames.
"""
from __future__ import annotations

import pytest
from pathlib import Path

from video_engine import VideoConfig, PALETAS, RESOLUCIONES
from video_engine.engine import VideoEngine
from video_engine.templates import CierreMercadoTemplate
from video_engine.utils import formatear_numero, formatear_variacion, fade


# =============================================================================
# VIDEOCONFIG
# =============================================================================
class TestVideoConfig:
    def test_default_values(self):
        config = VideoConfig(datos={"fecha": "x", "merval": {}, "sp500": {}})
        assert config.duracion == 12
        assert config.formato == "vertical"
        assert config.fps == 30

    def test_resolucion_vertical(self):
        config = VideoConfig(formato="vertical", datos={})
        assert config.resolucion == (1080, 1920)

    def test_resolucion_cuadrado(self):
        config = VideoConfig(formato="cuadrado", datos={})
        assert config.resolucion == (1080, 1080)

    def test_formato_invalido(self):
        config = VideoConfig(formato="no_existe", datos={})
        with pytest.raises(ValueError, match="Formato desconocido"):
            _ = config.resolucion

    def test_paleta_invalida(self):
        config = VideoConfig(paleta="no_existe", datos={})
        with pytest.raises(ValueError, match="Paleta desconocida"):
            _ = config.paleta_activa

    def test_total_frames(self):
        config = VideoConfig(duracion=10, fps=30, datos={})
        assert config.total_frames == 300


# =============================================================================
# FORMATEO
# =============================================================================
class TestFormateo:
    def test_formatear_numero_entero(self):
        assert formatear_numero(1847523) == "1.847.523"

    def test_formatear_numero_decimal(self):
        assert formatear_numero(5812.45, decimales=2) == "5.812,45"

    def test_formatear_variacion_positiva(self):
        assert formatear_variacion(2.34) == "+2,34%"

    def test_formatear_variacion_negativa(self):
        assert formatear_variacion(-0.42) == "-0,42%"

    def test_formatear_variacion_cero(self):
        assert formatear_variacion(0) == "+0,00%"


# =============================================================================
# ANIMACIÓN
# =============================================================================
class TestAnimacion:
    def test_fade_antes_de_ventana(self):
        assert fade(0.05, 0.15, 0.40) == 0.0

    def test_fade_despues_de_ventana(self):
        assert fade(0.80, 0.15, 0.40) == 1.0

    def test_fade_dentro_de_ventana(self):
        # progreso 0.275 está justo al medio de 0.15-0.40
        resultado = fade(0.275, 0.15, 0.40)
        assert 0.49 < resultado < 0.51


# =============================================================================
# PLANTILLA CIERRE MERCADO — validación de datos
# =============================================================================
class TestCierreMercadoTemplate:
    def _config_valida(self):
        return VideoConfig(
            datos={
                "fecha": "23 / 04 / 2026",
                "merval": {"precio": 1_000_000, "var_pct": 1.0},
                "sp500": {"precio": 5_000, "var_pct": -0.5},
            },
        )

    def test_valida_datos_ok(self):
        config = self._config_valida()
        template = CierreMercadoTemplate()
        template.validar_datos(config)  # no debe lanzar

    def test_datos_falta_fecha(self):
        config = VideoConfig(datos={
            "merval": {"precio": 1, "var_pct": 1},
            "sp500": {"precio": 1, "var_pct": 1},
        })
        template = CierreMercadoTemplate()
        with pytest.raises(ValueError, match="fecha"):
            template.validar_datos(config)

    def test_datos_falta_precio(self):
        config = VideoConfig(datos={
            "fecha": "x",
            "merval": {"var_pct": 1},   # falta precio
            "sp500": {"precio": 1, "var_pct": 1},
        })
        template = CierreMercadoTemplate()
        with pytest.raises(ValueError, match="precio"):
            template.validar_datos(config)

    def test_renderiza_frame_sin_error(self):
        config = self._config_valida()
        template = CierreMercadoTemplate()
        img = template.renderizar_frame(config, progreso=0.5)
        assert img.size == (1080, 1920)

    def test_formato_horizontal_aun_no_soportado(self):
        config = self._config_valida()
        config.formato = "horizontal"
        template = CierreMercadoTemplate()
        with pytest.raises(NotImplementedError):
            template.renderizar_frame(config, 0.5)


# =============================================================================
# ENGINE — test de integración (genera un video corto real)
# =============================================================================
class TestVideoEngine:
    def test_genera_video_corto(self, tmp_path):
        """Test de integración: genera un video de 2 segundos y verifica que exista."""
        config = VideoConfig(
            duracion=2,   # corto para no demorar el test
            fps=24,
            datos={
                "fecha": "23 / 04 / 2026",
                "merval": {"precio": 1_000_000, "var_pct": 1.0},
                "sp500": {"precio": 5_000, "var_pct": -0.5},
            },
        )
        output = tmp_path / "test.mp4"

        engine = VideoEngine(template=CierreMercadoTemplate())
        engine.generar(config, output_path=output)

        assert output.exists()
        assert output.stat().st_size > 1000  # al menos 1 KB
