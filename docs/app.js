/* app.js — interfaz de la aplicación web de «Física con fractales» (M Lopez P, 2026, licencia MIT).
   El cálculo está en fractales.js. La clave de la API solo vive en una variable de este módulo: no se guarda en el
   navegador y solo se envía a https://api.anthropic.com cuando se pulsa «Explicar». */
(function () {
  "use strict";
  const F = window.Fractales;
  const $ = id => document.getElementById(id);
  const fmt = (v, d) => Number(v).toFixed(d === undefined ? 3 : d).replace(".", ",");
  let ultimo = { tema: "ninguno", resultado: {} };
  let claveApi = "";                                   // en memoria; nunca se persiste

  function recordar(tema, resultado) {
    ultimo = { tema: tema, resultado: resultado };
    $("i-contexto").textContent = "Último resultado (" + tema + "): " + JSON.stringify(resultado, (k, v) => typeof v === "number" ? Math.round(v * 1e5) / 1e5 : v);
  }

  // ------------------------------------------------------------ pestañas
  document.querySelectorAll("nav button").forEach(b => b.addEventListener("click", () => {
    document.querySelectorAll("nav button").forEach(x => x.setAttribute("aria-selected", x === b ? "true" : "false"));
    document.querySelectorAll(".panel").forEach(p => p.classList.toggle("activo", p.id === b.dataset.pestana));
  }));
  function enlazarSalida(id, dec) {
    const e = $(id), o = $(id + "-v");
    e.addEventListener("input", () => { o.textContent = fmt(e.value, dec); });
  }

  // ------------------------------------------------------------ gráficas en lienzo
  function limpiar(cv) { const c = cv.getContext("2d"); c.fillStyle = "#fff"; c.fillRect(0, 0, cv.width, cv.height); c.fillStyle = "#14181f"; c.font = "12px system-ui"; return c; }

  function graficaLogLog(cv, series, ejeX, ejeY) {
    const c = limpiar(cv), m = { i: 62, d: 22, s: 14, b: 40 }, W = cv.width - m.i - m.d, H = cv.height - m.s - m.b;
    let xs = [], ys = [];
    series.forEach(s => s.x.forEach((v, i) => { if (v > 0 && s.y[i] > 0) { xs.push(Math.log10(v)); ys.push(Math.log10(s.y[i])); } }));
    const x0 = Math.floor(Math.min(...xs)), x1 = Math.ceil(Math.max(...xs)), y0 = Math.floor(Math.min(...ys)), y1 = Math.ceil(Math.max(...ys));
    const X = v => m.i + (Math.log10(v) - x0) / (x1 - x0 || 1) * W, Y = v => m.s + H - (Math.log10(v) - y0) / (y1 - y0 || 1) * H;
    c.strokeStyle = "#14181f"; c.lineWidth = 1.2; c.strokeRect(m.i, m.s, W, H);
    c.fillStyle = "#14181f"; c.font = "12px system-ui";
    for (let k = x0; k <= x1; k++) { const px = m.i + (k - x0) / (x1 - x0 || 1) * W; c.fillText("10^" + k, Math.min(px - 12, cv.width - 34), m.s + H + 16); }
    for (let k = y0; k <= y1; k++) { const py = m.s + H - (k - y0) / (y1 - y0 || 1) * H; c.fillText("10^" + k, 20, py + 4); }
    c.fillText(ejeX, m.i + W / 2 - 30, cv.height - 6);
    c.save(); c.translate(11, m.s + H / 2 + 30); c.rotate(-Math.PI / 2); c.fillText(ejeY, 0, 0); c.restore();
    series.forEach(s => {
      c.strokeStyle = s.color || "#14181f"; c.fillStyle = s.color || "#14181f"; c.lineWidth = 1.6;
      if (s.linea) { c.setLineDash(s.discontinua ? [6, 4] : []); c.beginPath(); s.x.forEach((v, i) => { const px = X(v), py = Y(s.y[i]); i ? c.lineTo(px, py) : c.moveTo(px, py); }); c.stroke(); c.setLineDash([]); }
      else s.x.forEach((v, i) => { if (v > 0 && s.y[i] > 0) { c.beginPath(); c.arc(X(v), Y(s.y[i]), 3.5, 0, 2 * Math.PI); c.stroke(); } });
    });
  }

  function indicesLog(n, k) {                 // k índices repartidos en escala logarítmica entre 1 y n − 1
    const out = new Set();
    for (let i = 0; i < k; i++) out.add(Math.min(n - 1, Math.round(Math.pow(n - 1, i / (k - 1)))));
    return [...out];
  }
  const tomar = (v, idx) => idx.map(i => v[i]);

  function recta(x, a) { return x.map(v => Math.exp(a.ordenada) * Math.pow(v, a.pendiente)); }

  function dibujarPuntos(cv, pts, n, opciones) {
    const c = limpiar(cv);
    let xmin = Infinity, xmax = -Infinity, ymin = Infinity, ymax = -Infinity;
    for (let k = 0; k < n; k++) { const x = pts[2 * k], y = pts[2 * k + 1]; if (x < xmin) xmin = x; if (x > xmax) xmax = x; if (y < ymin) ymin = y; if (y > ymax) ymax = y; }
    const esc = Math.min((cv.width - 20) / (xmax - xmin || 1), (cv.height - 20) / (ymax - ymin || 1));
    const ox = (cv.width - (xmax - xmin) * esc) / 2, oy = (cv.height - (ymax - ymin) * esc) / 2;
    c.strokeStyle = c.fillStyle = "#14181f"; c.lineWidth = 1;
    if (opciones && opciones.linea) { c.beginPath(); for (let k = 0; k < n; k++) { const px = ox + (pts[2 * k] - xmin) * esc, py = cv.height - oy - (pts[2 * k + 1] - ymin) * esc; k ? c.lineTo(px, py) : c.moveTo(px, py); } c.stroke(); }
    else for (let k = 0; k < n; k++) c.fillRect(ox + (pts[2 * k] - xmin) * esc, cv.height - oy - (pts[2 * k + 1] - ymin) * esc, 1, 1);
  }

  // ------------------------------------------------------------ 1. fractales
  enlazarSalida("f-nivel", 0);
  $("f-tipo").addEventListener("change", () => {
    const t = $("f-tipo").value;
    $("f-cre").parentElement.classList.toggle("visible", t === "julia");
    const n = $("f-nivel");
    if (t === "mandelbrot" || t === "julia") { n.min = 20; n.max = 500; n.step = 10; n.value = 150; }
    else if (t === "caos") { n.min = 1; n.max = 300; n.step = 1; n.value = 100; }
    else { n.min = 0; n.max = t === "sierpinski" ? 9 : 8; n.step = 1; n.value = 4; }
    $("f-nivel-v").textContent = n.value;
  });
  function dibujarFractal() {
    const t = $("f-tipo").value, n = +$("f-nivel").value, cv = $("f-lienzo"), c = limpiar(cv);
    let res = {};
    if (t === "koch") {
      const p = F.koch(n), flat = new Float64Array(p.flat());
      dibujarPuntos(cv, flat, p.length, { linea: true });
      res = { nivel: n, segmentos: Math.pow(4, n), longitud: Math.pow(4 / 3, n), D_teorica: F.semejanza(4, 1 / 3) };
    } else if (t === "cantor") {
      c.fillStyle = "#14181f";
      for (let k = 0; k <= n; k++) F.cantor(k).forEach(([a, b]) => c.fillRect(20 + a * (cv.width - 40), 20 + k * 50, Math.max((b - a) * (cv.width - 40), 1), 18));
      res = { nivel: n, intervalos: Math.pow(2, n), longitud: Math.pow(2 / 3, n), D_teorica: F.semejanza(2, 1 / 3) };
    } else if (t === "sierpinski") {
      const s = F.sierpinskiMascara(n), img = c.createImageData(s.ancho, s.alto);
      for (let i = 0; i < s.mascara.length; i++) { const v = s.mascara[i] ? 20 : 255; img.data.set([v, v, v, 255], 4 * i); }
      const tmp = document.createElement("canvas"); tmp.width = s.ancho; tmp.height = s.alto; tmp.getContext("2d").putImageData(img, 0, 0);
      c.imageSmoothingEnabled = false; const lado = Math.min(cv.width, cv.height) - 20; c.drawImage(tmp, (cv.width - lado) / 2, 10, lado, lado);
      res = { nivel: n, D_conteo_de_cajas: F.boxCounting(s.mascara, s.ancho, s.alto).D, D_teorica: F.semejanza(3, 0.5) };
    } else if (t === "caos") {
      const N = n * 1000, p = F.juegoDelCaos(N, 1);
      dibujarPuntos(cv, p, N);
      res = { puntos: N, D_teorica: F.semejanza(3, 0.5) };
    } else {
      const w = cv.width, h = cv.height, julia = t === "julia" ? [+$("f-cre").value, +$("f-cim").value] : null;
      const e = julia ? F.escape(w, h, -1.6, 1.6, -1.07, 1.07, n, julia) : F.escape(w, h, -2.4, 0.9, -1.1, 1.1, n, null);
      const img = c.createImageData(w, h);
      for (let i = 0; i < w * h; i++) { const v = e[i] >= n ? 0 : Math.round(255 - 200 * Math.log1p(e[i]) / Math.log1p(n)); img.data.set([v, v, v, 255], 4 * i); }
      c.putImageData(img, 0, 0);
      let dentro = 0; for (let i = 0; i < w * h; i++) if (e[i] >= n) dentro++;
      res = julia ? { c_real: julia[0], c_imag: julia[1], iteraciones: n, fraccion_que_no_escapa: dentro / (w * h) }
        : { iteraciones: n, area_estimada: dentro * (3.3 / w) * (2.2 / h) };
    }
    $("f-res").textContent = Object.entries(res).map(([k, v]) => k.replace(/_/g, " ") + ": " + (Number.isInteger(v) ? v : fmt(v, 4))).join(" · ");
    recordar("fractal " + t, res);
  }
  $("f-dibujar").addEventListener("click", dibujarFractal);

  // ------------------------------------------------------------ 2. dimensión
  enlazarSalida("d-umbral", 2);
  let fuente = null;                                    // {rgba, ancho, alto}
  function cargarPrueba() {
    const s = F.sierpinskiMascara(9), rgba = new Uint8ClampedArray(4 * s.mascara.length);
    for (let i = 0; i < s.mascara.length; i++) { const v = s.mascara[i] ? 0 : 255; rgba.set([v, v, v, 255], 4 * i); }
    fuente = { rgba: rgba, ancho: s.ancho, alto: s.alto, nombre: "Sierpinski de prueba (nivel 9)" };
    medir();
  }
  $("d-prueba").addEventListener("click", cargarPrueba);
  $("d-archivo").addEventListener("change", ev => {
    const f = ev.target.files[0]; if (!f) return;
    const url = URL.createObjectURL(f), im = new Image();
    im.onload = () => {
      const esc = Math.min(1, 1024 / Math.max(im.width, im.height));
      const w = Math.round(im.width * esc), h = Math.round(im.height * esc), cv = document.createElement("canvas");
      cv.width = w; cv.height = h; const c = cv.getContext("2d"); c.drawImage(im, 0, 0, w, h);
      fuente = { rgba: c.getImageData(0, 0, w, h).data, ancho: w, alto: h, nombre: f.name };
      URL.revokeObjectURL(url); medir();
    };
    im.src = url;
  });
  function medir() {
    if (!fuente) { cargarPrueba(); return; }
    const m = F.mascaraDeImagen(fuente.rgba, fuente.ancho, fuente.alto, +$("d-umbral").value, $("d-claro").checked);
    const r = F.boxCounting(m, fuente.ancho, fuente.alto);
    const cv = $("d-imagen"), c = limpiar(cv), img = c.createImageData(fuente.ancho, fuente.alto);
    for (let i = 0; i < m.length; i++) { const v = m[i] ? 20 : 255; img.data.set([v, v, v, 255], 4 * i); }
    const tmp = document.createElement("canvas"); tmp.width = fuente.ancho; tmp.height = fuente.alto; tmp.getContext("2d").putImageData(img, 0, 0);
    const esc = Math.min(cv.width / fuente.ancho, cv.height / fuente.alto);
    c.drawImage(tmp, 0, 0, fuente.ancho * esc, fuente.alto * esc);
    const a = { pendiente: -r.D, ordenada: r.ordenada };
    graficaLogLog($("d-grafica"), [{ x: r.tamanos, y: r.conteos }, { x: r.tamanos, y: recta(r.tamanos, a), linea: true, color: "#9a5b00" }], "lado de la caja s (px)", "N(s)");
    $("d-res").textContent = fuente.nombre + ": D = " + fmt(r.D, 3) + " (R² = " + fmt(r.r2, 4) + "), cajas de " + r.tamanos[0] + " a " + r.tamanos[r.tamanos.length - 1] + " px";
    recordar("dimension por conteo de cajas", { D: r.D, r2: r.r2, caja_min: r.tamanos[0], caja_max: r.tamanos[r.tamanos.length - 1], umbral: +$("d-umbral").value });
  }
  $("d-medir").addEventListener("click", medir);

  // ------------------------------------------------------------ 3. caminatas
  enlazarSalida("c-mu", 1); enlazarSalida("c-alfa", 1);
  $("c-simular").addEventListener("click", () => {
    const t = $("c-tipo").value, sem = +$("c-semilla").value;
    if (t === "browniano") {
      dibujarPuntos($("c-tray"), F.caminata(20000, sem), 20001, { linea: true });
      const m = F.msdBrowniano(1000, 1000, sem), a = F.exponente(m.t, m.msd, 10);
      const ix = indicesLog(m.t.length, 20);
      graficaLogLog($("c-msd"), [{ x: tomar(m.t, ix), y: tomar(m.msd, ix) }, { x: m.t, y: m.t, linea: true, discontinua: true, color: "#9a5b00" }], "pasos t", "⟨r²⟩");
      $("c-res").textContent = "Browniana: ⟨r²⟩ ∝ t^α con α = " + fmt(a.pendiente, 3) + " (teoría: 1; la recta discontinua es ⟨r²⟩ = t)";
      recordar("difusion: caminata browniana", { alfa: a.pendiente, caminantes: 1000, pasos: 1000 });
    } else if (t === "levy") {
      const mu = +$("c-mu").value;
      dibujarPuntos($("c-tray"), F.vueloLevy(3000, mu, sem), 3001, { linea: true });
      const m = F.medianaLevy(800, 400, mu, sem), a = F.exponente(m.t, m.mediana, 10);
      const ix = indicesLog(m.t.length, 20);
      graficaLogLog($("c-msd"), [{ x: tomar(m.t, ix), y: tomar(m.mediana, ix) }], "saltos t", "mediana de |r|");
      $("c-res").textContent = "Lévy μ = " + fmt(mu, 1) + ": la mediana crece como t^" + fmt(a.pendiente, 3) + " (teoría para μ < 2: 1/μ = " + fmt(1 / mu, 3) + ")";
      recordar("difusion: vuelo de Levy", { mu: mu, exponente_mediana: a.pendiente, teorico: 1 / mu });
    } else {
      const al = +$("c-alfa").value, m = F.ctrwMsd(600, 1e5, al, sem), a = F.exponente(m.t, m.msd);
      limpiar($("c-tray")).fillText("La CTRW se describe por su ⟨x²(t)⟩ →", 20, 30);
      graficaLogLog($("c-msd"), [{ x: m.t, y: m.msd }, { x: m.t, y: recta(m.t, a), linea: true, color: "#9a5b00" }], "tiempo", "⟨x²⟩");
      $("c-res").textContent = "CTRW con esperas de exponente " + fmt(al, 1) + ": ⟨x²⟩ ∝ t^α con α = " + fmt(a.pendiente, 3);
      recordar("difusion: CTRW", { alfa: a.pendiente, alfa_esperas: al });
    }
  });

  // ------------------------------------------------------------ 4. DLA
  let dla = null, trabajando = false;
  function pintarDLA() {
    const cv = $("a-lienzo"), c = cv.getContext("2d"), L = dla.lado, img = c.createImageData(L, L);
    for (let i = 0; i < L * L; i++) {
      const v = dla.g[i] ? Math.round(30 + 150 * dla.orden[i] / dla.n) : 255;
      img.data.set([v, v, v, 255], 4 * i);
    }
    c.putImageData(img, 0, 0);
  }
  $("a-crecer").addEventListener("click", () => {
    dla = new F.DLA(401, +$("a-semilla").value); trabajando = true;
    const objetivo = +$("a-n").value;
    (function paso() {
      if (!trabajando) return;
      const sigue = dla.anadir(Math.min(300, objetivo - dla.n));
      pintarDLA();
      $("a-res").textContent = dla.n + " partículas…";
      if (sigue && dla.n < objetivo) requestAnimationFrame(paso);
      else {
        trabajando = false;
        const r = dla.dimension();
        graficaLogLog($("a-grafica"), [{ x: r.radios, y: r.masas }, { x: r.radios, y: recta(r.radios, { pendiente: r.D, ordenada: Math.log(r.masas[0]) - r.D * Math.log(r.radios[0]) }), linea: true, color: "#9a5b00" }], "radio R (px)", "partículas en R");
        $("a-res").textContent = dla.n + " partículas: dimensión de masa D = " + fmt(r.D, 2) + " (R² = " + fmt(r.r2, 3) + "); referencia fuera de red ≈ 1,71";
        recordar("dimension de un agregado DLA", { D: r.D, r2: r.r2, particulas: dla.n, radio_de_giro: r.rg });
      }
    })();
  });
  $("a-parar").addEventListener("click", () => { trabajando = false; });

  // ------------------------------------------------------------ 5. percolación
  enlazarSalida("p-p", 4);
  function generarRed() {
    const L = +$("p-L").value, p = +$("p-p").value, m = F.redPercolacion(L, p, +$("p-semilla").value), cl = F.cumulos(m, L);
    let mayor = 0, et = 0; cl.tamanos.forEach((t, i) => { if (i && t > mayor) { mayor = t; et = i; } });
    const cv = $("p-lienzo"), c = cv.getContext("2d"), img = c.createImageData(L, L);
    for (let i = 0; i < L * L; i++) { const v = cl.etiquetas[i] === et && et ? 0 : m[i] ? 160 : 255; img.data.set([v, v, v, 255], 4 * i); }
    const tmp = document.createElement("canvas"); tmp.width = L; tmp.height = L; tmp.getContext("2d").putImageData(img, 0, 0);
    c.imageSmoothingEnabled = false; c.drawImage(tmp, 0, 0, cv.width, cv.height);
    const cr = F.cruza(m, L);
    $("p-res").textContent = "L = " + L + ", p = " + fmt(p, 4) + ": " + cl.n + " cúmulos; el mayor tiene " + mayor + " casillas (" + fmt(100 * mayor / (L * L), 1) + " %) y " + (cr ? "sí" : "no") + " cruza de arriba abajo";
    recordar("percolacion en red cuadrada", { L: L, p: p, cumulos: cl.n, fraccion_mayor: mayor / (L * L), cruza: cr });
  }
  $("p-red").addEventListener("click", generarRed);
  $("p-barrido").addEventListener("click", () => {
    const L = Math.min(+$("p-L").value, 96), ps = []; for (let i = 0; i <= 10; i++) ps.push(0.55 + 0.01 * i);
    const P = F.probCruce(L, ps, 80, +$("p-semilla").value), pc = F.umbralCruce(ps, P);
    const cv = $("p-grafica"), c = limpiar(cv), m = 45, W = cv.width - m - 15, H = cv.height - 60;
    c.strokeStyle = c.fillStyle = "#14181f"; c.lineWidth = 1.2; c.strokeRect(m, 15, W, H); c.font = "12px system-ui";
    c.beginPath(); ps.forEach((p, i) => { const x = m + (p - 0.55) / 0.1 * W, y = 15 + H - P[i] * H; i ? c.lineTo(x, y) : c.moveTo(x, y); }); c.stroke();
    ps.forEach((p, i) => { c.beginPath(); c.arc(m + (p - 0.55) / 0.1 * W, 15 + H - P[i] * H, 3.5, 0, 2 * Math.PI); c.stroke(); });
    c.setLineDash([4, 4]); c.beginPath(); c.moveTo(m, 15 + H / 2); c.lineTo(m + W, 15 + H / 2); c.stroke(); c.setLineDash([]);
    c.fillText("0,55", m - 10, 15 + H + 16); c.fillText("0,65", m + W - 20, 15 + H + 16); c.fillText("p", m + W / 2, 15 + H + 30);
    c.fillText("1", m - 14, 20); c.fillText("0", m - 14, 15 + H);
    $("p-res").textContent = "Barrido con L = " + L + " y 80 redes por punto: probabilidad de cruce 1/2 en p ≈ " + fmt(pc, 3) + " (referencia ≈ 0,5927)";
    recordar("umbral de percolacion", { L: L, pc_estimado: pc, muestras: 80 });
  });

  // ------------------------------------------------------------ 6. caos
  enlazarSalida("k-r", 3);
  $("k-calcular").addEventListener("click", () => {
    if ($("k-tipo").value === "logistico") {
      const r = +$("k-r").value, b = F.bifurcacion(2.8, 4, 360, 400, 80), cv = $("k-lienzo"), c = limpiar(cv);
      c.fillStyle = "#14181f";
      for (let i = 0; i < b.r.length; i++) c.fillRect((b.r[i] - 2.8) / 1.2 * (cv.width - 1), (1 - b.x[i]) * (cv.height - 1), 1, 1);
      c.strokeStyle = "#9a5b00"; c.beginPath(); const xr = (r - 2.8) / 1.2 * cv.width; c.moveTo(xr, 0); c.lineTo(xr, cv.height); c.stroke();
      const g = $("k-grafica"), cg = limpiar(g); cg.strokeStyle = "#14181f"; cg.beginPath();
      for (let i = 0; i <= 300; i++) { const rr = 2.8 + 1.2 * i / 300, l = Math.max(-2, F.lyapunovLogistico(rr, 3000, 300)); const x = i / 300 * g.width, y = g.height * (1 - (l + 2) / 3); i ? cg.lineTo(x, y) : cg.moveTo(x, y); }
      cg.stroke(); cg.setLineDash([5, 4]); cg.beginPath(); cg.moveTo(0, g.height * (1 - 2 / 3)); cg.lineTo(g.width, g.height * (1 - 2 / 3)); cg.stroke(); cg.setLineDash([]);
      const lam = F.lyapunovLogistico(r);
      $("k-res").textContent = "r = " + fmt(r, 3) + ": λ = " + fmt(lam, 3) + (lam > 0 ? " (caótico)" : " (periódico)") + ". Arriba: bifurcación; derecha: λ(r) entre −2 y 1 (línea discontinua: λ = 0).";
      recordar("caos: mapa logistico", { r: r, lyapunov: lam });
    } else {
      const p = F.lorenz(8000, 0.01), cv = $("k-lienzo"), c = limpiar(cv);
      c.strokeStyle = "#14181f"; c.lineWidth = 0.8; c.beginPath();
      for (let k = 0; k < 8000; k++) { const x = (p[3 * k] + 22) / 44 * cv.width, y = cv.height - p[3 * k + 2] / 52 * cv.height; k ? c.lineTo(x, y) : c.moveTo(x, y); }
      c.stroke();
      const a = F.lorenz(4000, 0.01, [1, 1, 1]), b = F.lorenz(4000, 0.01, [1 + 1e-8, 1, 1]), t = [], d = [];
      for (let k = 0; k < 4000; k += 20) { t.push((k + 1) * 0.01); d.push(Math.hypot(a[3 * k] - b[3 * k], a[3 * k + 1] - b[3 * k + 1], a[3 * k + 2] - b[3 * k + 2]) + 1e-12); }
      const g = $("k-grafica"), cg = limpiar(g); cg.strokeStyle = "#14181f"; cg.beginPath();
      t.forEach((v, i) => { const x = v / 40 * g.width, y = g.height * (1 - (Math.log10(d[i]) + 10) / 12); i ? cg.lineTo(x, y) : cg.moveTo(x, y); }); cg.stroke();
      const lam = F.lyapunovLorenz(300, 0.01);
      $("k-res").textContent = "Lorenz (σ = 10, ρ = 28, β = 8/3): λ ≈ " + fmt(lam, 3) + " con 300 unidades de tiempo (referencia ≈ 0,9056). Derecha: distancia entre dos trayectorias separadas 10⁻⁸, en escala logarítmica de 10⁻¹⁰ a 10².";
      recordar("caos: atractor de Lorenz", { lyapunov: lam, tiempo: 300, dt: 0.01 });
    }
  });

  // ------------------------------------------------------------ 7. difusión fraccionaria
  enlazarSalida("x-alfa", 2);
  $("x-resolver").addEventListener("click", () => {
    const al = +$("x-alfa").value, r = F.difusionFraccionaria(al, { nt: +$("x-nt").value });
    const cv = $("x-perfiles"), c = limpiar(cv), est = [[], [6, 4], [2, 3], [10, 3, 2, 3]];
    let max = 0; Object.values(r.perfiles).forEach(u => u.forEach(v => { if (v > max) max = v; }));
    c.font = "12px system-ui";
    Object.entries(r.perfiles).forEach(([t, u], k) => {
      c.strokeStyle = "#14181f"; c.setLineDash(est[k % 4]); c.lineWidth = 1.6; c.beginPath();
      u.forEach((v, i) => { const x = (r.x[i] + 6) / 12 * cv.width, y = cv.height - 20 - v / max * (cv.height - 40); if (r.x[i] >= -6 && r.x[i] <= 6) (i && r.x[i - 1] >= -6) ? c.lineTo(x, y) : c.moveTo(x, y); });
      c.stroke(); c.setLineDash([]); c.fillText("t = " + t.replace(".", ","), cv.width - 90, 20 + 16 * k);
    });
    const sel = indicesLog(r.t.length, 16);
    graficaLogLog($("x-msd"), [{ x: sel.map(i => r.t[i]), y: sel.map(i => r.msd[i]) }, { x: r.t.slice(1), y: r.t.slice(1).map(v => r.coefTeorico * Math.pow(v, al)), linea: true, discontinua: true, color: "#9a5b00" }], "t", "⟨x²⟩");
    $("x-res").textContent = "α = " + fmt(al, 2) + ": exponente ajustado " + fmt(r.alfaAjustado, 3) + ", coeficiente " + fmt(r.coefAjustado, 3) + " (teoría 2K/Γ(1 + α) = " + fmt(r.coefTeorico, 3) + ")";
    recordar("difusion fraccionaria", { alfa: r.alfaAjustado, alfa_ecuacion: al, coef: r.coefAjustado, coef_teorico: r.coefTeorico });
  });

  // ------------------------------------------------------------ 8. IA
  $("i-clave").addEventListener("input", e => { claveApi = e.target.value.trim(); });
  $("i-borrar").addEventListener("click", () => { claveApi = ""; $("i-clave").value = ""; $("i-respuesta").textContent = "Clave olvidada."; });
  const SISTEMA = "Eres un tutor de física que ayuda a usar el simulador del libro «Física con fractales». Responde en español, con frases cortas. " +
    "Reglas: 1) No calcules cifras nuevas: usa solo los números que te da el usuario. 2) Distingue lo simulado de lo teórico. " +
    "3) Di las hipótesis del modelo y cuándo deja de valer. 4) Si no estás seguro, dilo. 5) Termina con comprobaciones que se puedan hacer con el simulador.";
  async function explicar() {
    const salida = $("i-respuesta"), pregunta = $("i-pregunta").value.trim();
    if (!claveApi) { salida.textContent = F.explicacionLocal(ultimo.tema, ultimo.resultado); return; }
    salida.textContent = "Consultando a la IA…";
    const cuerpo = { model: "claude-sonnet-5-5", max_tokens: 2000, system: SISTEMA,
      messages: [{ role: "user", content: "Tema: " + ultimo.tema + "\nResultado del simulador (JSON): " + JSON.stringify(ultimo.resultado) + "\nPregunta: " + pregunta }] };
    try {
      const r = await fetch("https://api.anthropic.com/v1/messages", { method: "POST", referrerPolicy: "no-referrer", credentials: "omit",
        headers: { "content-type": "application/json", "x-api-key": claveApi, "anthropic-version": "2023-06-01", "anthropic-dangerous-direct-browser-access": "true" },
        body: JSON.stringify(cuerpo) });
      const d = await r.json();
      if (!r.ok) { salida.textContent = "Error de la API (" + r.status + "): " + ((d.error && d.error.message) || "sin detalle") + ". Puedes usar el modo sin clave."; return; }
      if (d.stop_reason === "refusal") { salida.textContent = "La IA ha declinado responder. Usa el modo sin clave."; return; }
      salida.textContent = d.content.filter(b => b.type === "text").map(b => b.text).join("\n") +
        "\n\n— Respuesta generada por IA: compruébala con el simulador antes de usarla.";
    } catch (e) {
      salida.textContent = "No se pudo conectar con la API (" + e.message + "). Se muestra la explicación sin clave:\n\n" + F.explicacionLocal(ultimo.tema, ultimo.resultado);
    }
  }
  $("i-explicar").addEventListener("click", explicar);

  dibujarFractal();
  recordar("fractal koch", ultimo.resultado);

  // enlaces directos: index.html#dla abre la pestaña y ejecuta su cálculo principal
  const AUTO = { dimension: "d-prueba", caminatas: "c-simular", dla: "a-crecer", percolacion: "p-red", caos: "k-calcular", fraccionaria: "x-resolver" };
  const h = location.hash.slice(1);
  const pest = document.querySelector('nav button[data-pestana="' + h + '"]');
  if (pest) { pest.click(); if (AUTO[h]) $(AUTO[h]).click(); }
})();
