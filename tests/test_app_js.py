"""Ejecuta las pruebas de la aplicación web (docs/fractales.js) con Node, si está instalado."""
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(shutil.which("node") is None, reason="Node no está instalado")
def test_fractales_js():
    r = subprocess.run(["node", str(RAIZ / "tests" / "app.test.js")], capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stdout + r.stderr


def test_app_no_guarda_la_clave():
    js = (RAIZ / "docs" / "app.js").read_text(encoding="utf-8")
    assert "localStorage" not in js and "sessionStorage" not in js and "document.cookie" not in js
    assert "https://api.anthropic.com/v1/messages" in js
    html = (RAIZ / "docs" / "index.html").read_text(encoding="utf-8")
    assert "connect-src https://api.anthropic.com" in html     # la política de la página no deja enviar datos a otro sitio
