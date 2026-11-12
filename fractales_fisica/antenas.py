"""Antenas fractales: geometría de prefractales de Koch y Sierpinski.

El libro solo calcula geometría (longitud de hilo, área ocupada, razones de escala) y la longitud de un monopolo
de cuarto de onda de referencia. La frecuencia de resonancia real de una antena fractal depende de la forma, del
sustrato y de la alimentación y se obtiene con un simulador electromagnético (p. ej. NEC u openEMS) o midiendo;
no es proporcional a la longitud total del hilo.
"""
from __future__ import annotations

C_LUZ = 299_792_458.0


def longitud_koch(nivel: int, lado: float = 1.0) -> float:
    """Longitud de la curva de Koch de nivel n sobre un segmento: lado · (4/3)^n."""
    return lado * (4 / 3) ** nivel


def monopolo_cuarto_onda(frecuencia_hz: float) -> float:
    """Longitud de un monopolo de λ/4 en el vacío: c / (4 f), en metros."""
    return C_LUZ / (4 * frecuencia_hz)


def bandas_log_periodicas(f0_hz: float, razon: float, n: int) -> list[float]:
    """Frecuencias f0 · razon^k: las bandas que sugiere una estructura autosemejante de razón de escala `razon`."""
    return [f0_hz * razon ** k for k in range(n)]


def area_sierpinski(nivel: int) -> float:
    """Fracción del área del triángulo que conserva el metal en el gasket de Sierpinski de nivel n: (3/4)^n."""
    return (3 / 4) ** nivel


def perimetro_sierpinski(nivel: int, lado: float = 1.0) -> float:
    """Perímetro total de los bordes del gasket de nivel n: 3 · lado · (3/2)^n."""
    return 3 * lado * (3 / 2) ** nivel
