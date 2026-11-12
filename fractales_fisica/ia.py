"""Asistente de IA opcional (API de Anthropic, modelo claude-sonnet-5-5) para explicar un resultado del simulador,
revisar una derivación o proponer un modelo fractal.

Reglas del módulo:
- La clave se lee SOLO de la variable de entorno ANTHROPIC_API_KEY. Nunca se escribe en disco ni se imprime.
- Sin clave (o sin el paquete `anthropic`), todo funciona en «modo sin clave»: devuelve una explicación local
  generada con plantillas a partir del propio resultado y la lista de comprobaciones.
- La IA no calcula: el mensaje le pasa los números del simulador y le pide que no invente otros. Cualquier cifra
  que proponga se comprueba con `verificar_afirmacion`, que la recalcula con este paquete.
"""
from __future__ import annotations

import json
import math
import os

MODELO = "claude-sonnet-5-5"

SISTEMA = (
    "Eres un tutor de física que ayuda a usar el paquete Python fractales_fisica. Responde en español, con frases "
    "cortas. Reglas: 1) No calcules cifras nuevas: usa solo los números que te da el usuario y, si hace falta otro, "
    "di qué función del paquete lo calcula. 2) Distingue lo medido, lo simulado y lo teórico. 3) Señala las hipótesis "
    "del modelo y cuándo deja de valer. 4) Si no estás seguro, dilo. 5) Termina con una lista de comprobaciones que "
    "el usuario puede hacer con el simulador."
)

COMPROBACIONES = {
    "dimension": ["Repite el conteo de cajas con otro rango de tamaños y mira si D cambia más de 0,05.",
                  "Prueba primero con un fractal de dimensión conocida (Sierpinski: log 3 / log 2).",
                  "Comprueba que R² del ajuste log-log es alto, pero recuerda que un R² alto no prueba una ley de potencias."],
    "caos": ["Cambia el paso de integración a la mitad y comprueba que el exponente apenas cambia.",
             "Alarga el tiempo de promedio: el exponente de Lyapunov converge despacio.",
             "Compara con un valor publicado citado en el libro, no con la memoria del asistente."],
    "difusion": ["Ajusta el exponente solo en el tramo intermedio: ni los primeros pasos ni cuando se notan los bordes.",
                 "Comprueba con α = 1 que sale difusión normal (⟨x²⟩ = 2Kt).",
                 "Promedia más trayectorias y mira cuánto se mueve la estimación."],
    "general": ["Recalcula con otra semilla aleatoria.", "Cambia la resolución y mira si el resultado converge.",
                "Comprueba las unidades de cada término de la ecuación."],
}


def hay_clave() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())


def _resumen(resultado: dict) -> str:
    limpio = {}
    for k, v in resultado.items():
        if isinstance(v, float):
            limpio[k] = round(v, 6)
        elif isinstance(v, (int, str, bool)) or v is None:
            limpio[k] = v
        elif isinstance(v, (list, tuple)) and len(v) <= 20 and all(isinstance(x, (int, float)) for x in v):
            limpio[k] = [round(float(x), 6) for x in v]
    return json.dumps(limpio, ensure_ascii=False)


def explicacion_local(tema: str, resultado: dict) -> str:
    """Modo sin clave: explicación con plantillas, sin conexión."""
    lineas = [f"Modo sin clave (no se ha usado ninguna IA). Resultado del simulador sobre «{tema}»:"]
    for k, v in json.loads(_resumen(resultado)).items():
        lineas.append(f"  - {k}: {v}")
    if "D" in resultado:
        lineas.append("Una dimensión D entre 1 y 2 indica una curva que llena el plano más que una línea y menos que una superficie.")
    if "alfa" in resultado:
        a = resultado["alfa"]
        tipo = "subdifusión" if a < 0.95 else ("superdifusión" if a > 1.05 else "difusión normal")
        lineas.append(f"Un exponente α ≈ {a:.2f} en ⟨x²⟩ ∝ t^α corresponde a {tipo}.")
    if "lyapunov" in resultado:
        lineas.append("Un exponente de Lyapunov positivo indica sensibilidad a las condiciones iniciales (caos).")
    lineas.append("Comprobaciones recomendadas:")
    clave = next((k for k in COMPROBACIONES if k in tema), "general")
    lineas += [f"  {i}. {c}" for i, c in enumerate(COMPROBACIONES[clave], 1)]
    return "\n".join(lineas)


def _llamar(mensaje: str, max_tokens: int = 2000) -> str:
    import anthropic

    cliente = anthropic.Anthropic()          # lee ANTHROPIC_API_KEY del entorno
    try:
        r = cliente.beta.messages.create(
            model=MODELO,
            max_tokens=max_tokens,
            system=SISTEMA,
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": mensaje}],
        )
    except anthropic.AuthenticationError:
        return "Error: la clave de ANTHROPIC_API_KEY no es válida."
    except anthropic.RateLimitError:
        return "Error: límite de uso de la API alcanzado; espera un poco y repite."
    except anthropic.APIStatusError as e:
        return f"Error de la API ({e.status_code}). Usa el modo sin clave o repite más tarde."
    except anthropic.APIConnectionError:
        return "Error: no hay conexión con la API. Usa el modo sin clave."
    if r.stop_reason == "refusal":
        return "La IA ha declinado responder. Usa el modo sin clave."
    return "".join(b.text for b in r.content if b.type == "text").strip()


def explicar(tema: str, resultado: dict, pregunta: str | None = None, forzar_local: bool = False) -> str:
    """Explica un resultado del simulador. Sin clave, devuelve la explicación local."""
    if forzar_local or not hay_clave():
        return explicacion_local(tema, resultado)
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return explicacion_local(tema, resultado) + "\n(Instala `anthropic` para usar la IA.)"
    msg = (f"Tema: {tema}.\nResultado del simulador (JSON): {_resumen(resultado)}\n"
           f"Pregunta: {pregunta or 'Explica qué significa este resultado, qué hipótesis tiene y cómo lo compruebo.'}")
    return _llamar(msg)


def revisar_derivacion(texto: str) -> str:
    """Pide a la IA que busque errores en una derivación (unidades, signos, pasos sin justificar)."""
    if not hay_clave():
        return ("Modo sin clave. Lista de revisión manual: 1) unidades de cada término; 2) límites conocidos (α = 1, D entero); "
                "3) signos; 4) cada aproximación, con su condición de validez; 5) contraste numérico con el simulador.")
    return _llamar("Revisa esta derivación paso a paso. Señala cada error de unidades, de signo o de lógica, y los pasos "
                   "que necesitan una hipótesis. No la reescribas entera.\n\n" + texto)


# ------------------------------------------------------------------ verificación de afirmaciones
def _valores_de_referencia() -> dict:
    from . import caos, dimension, percolacion
    import numpy as np
    return {
        "dimension_koch": lambda: dimension.dimension_semejanza(4, 1 / 3),
        "dimension_cantor": lambda: dimension.dimension_semejanza(2, 1 / 3),
        "dimension_sierpinski": lambda: dimension.dimension_semejanza(3, 1 / 2),
        "dimension_alfombra": lambda: dimension.dimension_semejanza(8, 1 / 3),
        "feigenbaum_delta": lambda: caos.feigenbaum(11)["delta"],
        "feigenbaum_alfa": lambda: caos.feigenbaum(11)["alfa"],
        "lyapunov_logistico_r4": lambda: caos.lyapunov_logistico(4.0),
        "umbral_percolacion_cuadrada": lambda: percolacion.umbral_por_cruce(64, np.linspace(0.55, 0.65, 11), 100)["pc"],
    }


def verificar_afirmacion(clave: str, valor_afirmado: float, tolerancia_rel: float = 0.01) -> dict:
    """Recalcula con el simulador la magnitud `clave` y la compara con lo que afirma la IA (o cualquiera)."""
    tabla = _valores_de_referencia()
    if clave not in tabla:
        return {"clave": clave, "estado": "desconocida", "disponibles": sorted(tabla)}
    v = float(tabla[clave]())
    ok = math.isclose(v, valor_afirmado, rel_tol=tolerancia_rel)
    return {"clave": clave, "simulador": v, "afirmado": valor_afirmado, "estado": "coincide" if ok else "NO coincide"}
