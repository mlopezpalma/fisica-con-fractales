"""Línea de órdenes: python -m fractales_fisica <cálculo> [opciones] [--ia]

Ejemplos:
  python -m fractales_fisica koch --nivel 6
  python -m fractales_fisica imagen hoja.png --umbral 0.5
  python -m fractales_fisica feigenbaum
  python -m fractales_fisica lorenz --tiempo 500
  python -m fractales_fisica difusion --alfa 0.6 --ia
  python -m fractales_fisica hurst serie.csv
  python -m fractales_fisica verificar feigenbaum_delta 4.67
  python -m fractales_fisica figuras --carpeta figuras

Con --ia se pide a la IA que explique el resultado (necesita ANTHROPIC_API_KEY en el entorno; sin ella, se usa la
explicación local). La clave no se guarda en ningún archivo.
"""
from __future__ import annotations

import argparse
import json
import math
import sys

import numpy as np

from . import aleatorio, caos, conjuntos, dimension, dla, fraccionario, ia, percolacion, series


def leer_imagen(ruta: str, umbral: float, invertir: bool) -> np.ndarray:
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Para leer imágenes instala Pillow: pip install pillow")
    a = np.asarray(Image.open(ruta).convert("L"), float) / 255.0
    ocupado = a < umbral          # por defecto, lo oscuro es el objeto
    return ~ocupado if invertir else ocupado


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m fractales_fisica", description="Simulador de física con fractales")
    sub = ap.add_subparsers(dest="orden", required=True)
    s = sub.add_parser("koch"); s.add_argument("--nivel", type=int, default=6)
    s = sub.add_parser("sierpinski"); s.add_argument("--nivel", type=int, default=9)
    s = sub.add_parser("imagen"); s.add_argument("ruta"); s.add_argument("--umbral", type=float, default=0.5)
    s.add_argument("--invertir", action="store_true")
    sub.add_parser("feigenbaum")
    s = sub.add_parser("logistico"); s.add_argument("--r", type=float, default=4.0)
    s = sub.add_parser("lorenz"); s.add_argument("--tiempo", type=float, default=500.0)
    s = sub.add_parser("caminata"); s.add_argument("--caminantes", type=int, default=2000); s.add_argument("--pasos", type=int, default=1000)
    s = sub.add_parser("levy"); s.add_argument("--mu", type=float, default=1.5)
    s = sub.add_parser("dla"); s.add_argument("--particulas", type=int, default=3000); s.add_argument("--semilla", type=int, default=11)
    s = sub.add_parser("percolacion"); s.add_argument("--L", type=int, default=64)
    s = sub.add_parser("difusion"); s.add_argument("--alfa", type=float, default=0.6)
    s = sub.add_parser("hurst"); s.add_argument("ruta", help="CSV o texto con una columna de números")
    s = sub.add_parser("verificar"); s.add_argument("clave"); s.add_argument("valor", type=float)
    s = sub.add_parser("figuras"); s.add_argument("--carpeta", default="figuras")
    for p in sub.choices.values():
        p.add_argument("--ia", action="store_true", help="explicar el resultado con IA (o en modo sin clave)")
        p.add_argument("--pregunta", default=None)
    a = ap.parse_args(argv)

    tema, res = a.orden, {}
    if a.orden == "koch":
        img = dimension.rasterizar(conjuntos.koch(a.nivel), 2048)
        res = dimension.box_counting(img) | {"D_teorica": dimension.dimension_semejanza(4, 1 / 3)}
        tema = "dimension de la curva de Koch"
    elif a.orden == "sierpinski":
        res = dimension.box_counting(conjuntos.sierpinski(a.nivel)) | {"D_teorica": dimension.dimension_semejanza(3, 0.5)}
        tema = "dimension del triangulo de Sierpinski"
    elif a.orden == "imagen":
        res = dimension.box_counting(leer_imagen(a.ruta, a.umbral, a.invertir))
        tema = "dimension por conteo de cajas de una imagen"
    elif a.orden == "feigenbaum":
        f = caos.feigenbaum(11)
        res = {"delta": f["delta"], "alfa_feigenbaum": f["alfa"], "r_inf": f["r_inf"]}
        tema = "caos: constantes de Feigenbaum"
    elif a.orden == "logistico":
        res = {"r": a.r, "lyapunov": caos.lyapunov_logistico(a.r)}
        tema = "caos: exponente de Lyapunov del mapa logistico"
    elif a.orden == "lorenz":
        res = {"lyapunov": caos.lyapunov_lorenz(a.tiempo)}
        tema = "caos: atractor de Lorenz"
    elif a.orden == "caminata":
        t, m = aleatorio.msd_conjunto(a.caminantes, a.pasos)
        res = aleatorio.exponente_msd(t, m, 10)
        tema = "difusion: caminata aleatoria"
    elif a.orden == "levy":
        r = aleatorio.escala_levy(2000, 1000, a.mu)
        res = {"mu": a.mu, "exponente_mediana": r["exponente"], "teorico": 1 / a.mu}
        tema = "difusion: vuelo de Levy"
    elif a.orden == "dla":
        g = dla.dla(a.particulas, a.semilla)
        c = g.shape[0] // 2
        res = dimension.masa_radio(g, (c, c), np.geomspace(4, dla.radio_de_giro(g), 8))
        tema = "dimension de un agregado DLA"
    elif a.orden == "percolacion":
        res = percolacion.umbral_por_cruce(a.L, np.linspace(0.55, 0.65, 11), 100)
        tema = "percolacion en red cuadrada"
    elif a.orden == "difusion":
        r = fraccionario.difusion_fraccionaria(a.alfa)
        res = {"alfa": r["alfa_ajustado"], "alfa_ecuacion": a.alfa, "coef": r["coef_ajustado"], "coef_teorico": r["coef_teorico"]}
        tema = "difusion fraccionaria"
    elif a.orden == "hurst":
        x = np.loadtxt(a.ruta, delimiter="," if a.ruta.endswith(".csv") else None, ndmin=1)
        res = {"H_rs": series.hurst_rs(x)["H"], "alfa_dfa": series.dfa(x)["alfa"], "n": len(x)}
        tema = "series: exponente de Hurst"
    elif a.orden == "verificar":
        res = ia.verificar_afirmacion(a.clave, a.valor)
        tema = "verificacion de una cifra"
    elif a.orden == "figuras":
        from .figuras import generar_todas
        res = {"figuras": len(generar_todas(a.carpeta))}

    salida = {k: v for k, v in res.items() if not isinstance(v, (list, np.ndarray))}
    print(json.dumps(salida, ensure_ascii=False, indent=1, default=lambda o: float(o) if math.isfinite(o) else str(o)))
    if a.ia:
        print()
        print(ia.explicar(tema, res, a.pregunta))
    return 0


if __name__ == "__main__":
    sys.exit(main())
