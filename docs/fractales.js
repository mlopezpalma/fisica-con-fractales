/* fractales.js — cálculo de la aplicación web de «Física con fractales» (M Lopez P, 2026, licencia MIT).
   Funciones puras, sin acceso a la página: las usa app.js en el navegador y las prueba Node (tests/app.test.js).
   Son traducciones directas de las funciones del paquete Python fractales_fisica. */
(function (raiz, fabrica) {
  if (typeof module === "object" && module.exports) module.exports = fabrica();
  else raiz.Fractales = fabrica();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // ------------------------------------------------------------ utilidades
  function aleatorio(semilla) {            // mulberry32: generador reproducible
    let a = semilla >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function ajusteLogLog(x, y) {
    const lx = [], ly = [];
    for (let i = 0; i < x.length; i++) {
      if (x[i] > 0 && y[i] > 0) { lx.push(Math.log(x[i])); ly.push(Math.log(y[i])); }
    }
    const n = lx.length;
    const mx = lx.reduce((a, b) => a + b, 0) / n, my = ly.reduce((a, b) => a + b, 0) / n;
    let sxy = 0, sxx = 0, syy = 0;
    for (let i = 0; i < n; i++) { sxy += (lx[i] - mx) * (ly[i] - my); sxx += (lx[i] - mx) ** 2; syy += (ly[i] - my) ** 2; }
    const b = sxy / sxx, a = my - b * mx;
    let ssr = 0;
    for (let i = 0; i < n; i++) ssr += (ly[i] - (a + b * lx[i])) ** 2;
    return { pendiente: b, ordenada: a, r2: syy > 0 ? 1 - ssr / syy : 1 };
  }

  function semejanza(n, r) { return Math.log(n) / Math.log(1 / r); }

  // ------------------------------------------------------------ conjuntos
  function cantor(nivel) {
    let t = [[0, 1]];
    for (let k = 0; k < nivel; k++) {
      const nuevo = [];
      for (const [a, b] of t) { const d = (b - a) / 3; nuevo.push([a, a + d], [b - d, b]); }
      t = nuevo;
    }
    return t;
  }

  function koch(nivel) {
    let p = [[0, 0], [1, 0]];
    const c = 0.5, s = Math.sqrt(3) / 2;
    for (let k = 0; k < nivel; k++) {
      const q = [p[0]];
      for (let i = 0; i < p.length - 1; i++) {
        const [ax, ay] = p[i], [bx, by] = p[i + 1];
        const dx = (bx - ax) / 3, dy = (by - ay) / 3;
        const p1 = [ax + dx, ay + dy], p3 = [ax + 2 * dx, ay + 2 * dy];
        const p2 = [p1[0] + c * dx - s * dy, p1[1] + s * dx + c * dy];
        q.push(p1, p2, p3, [bx, by]);
      }
      p = q;
    }
    return p;
  }

  function juegoDelCaos(n, semilla, razon) {
    const r = aleatorio(semilla || 1), f = razon || 0.5;
    const v = [[0, 0], [1, 0], [0.5, Math.sqrt(3) / 2]];
    const out = new Float64Array(2 * n);
    let x = 0.3, y = 0.3;
    for (let k = 0; k < n; k++) {
      const w = v[Math.floor(r() * 3)];
      x += f * (w[0] - x); y += f * (w[1] - y);
      out[2 * k] = x; out[2 * k + 1] = y;
    }
    return out;
  }

  function sierpinskiMascara(nivel) {          // triángulo de Pascal módulo 2
    const n = 1 << nivel, m = new Uint8Array(n * n);
    for (let i = 0; i < n; i++) for (let j = 0; j <= i; j++) if ((i & j) === j) m[i * n + j] = 1;
    return { mascara: m, ancho: n, alto: n };
  }

  function escape(w, h, x0, x1, y0, y1, maxIter, cJulia) {
    const out = new Uint16Array(w * h);
    for (let j = 0; j < h; j++) {
      const yi = y1 - (j / (h - 1)) * (y1 - y0);
      for (let i = 0; i < w; i++) {
        const xi = x0 + (i / (w - 1)) * (x1 - x0);
        let zr, zi, cr, ci;
        if (cJulia) { zr = xi; zi = yi; cr = cJulia[0]; ci = cJulia[1]; } else { zr = 0; zi = 0; cr = xi; ci = yi; }
        let k = 0;
        while (k < maxIter && zr * zr + zi * zi <= 4) {
          const t = zr * zr - zi * zi + cr;
          zi = 2 * zr * zi + ci; zr = t; k++;
        }
        out[j * w + i] = k;
      }
    }
    return out;
  }

  // ------------------------------------------------------------ dimensión
  function boxCounting(mascara, ancho, alto, tamanos) {
    const lado = Math.min(ancho, alto);
    if (!tamanos) { tamanos = []; for (let s = 2; s <= lado / 4; s *= 2) tamanos.push(s); }
    const conteos = [];
    for (const s of tamanos) {
      const nx = Math.floor(ancho / s), ny = Math.floor(alto / s);
      let c = 0;
      for (let by = 0; by < ny; by++) for (let bx = 0; bx < nx; bx++) {
        let hay = false;
        for (let y = by * s; y < (by + 1) * s && !hay; y++) {
          const fila = y * ancho;
          for (let x = bx * s; x < (bx + 1) * s; x++) if (mascara[fila + x]) { hay = true; break; }
        }
        if (hay) c++;
      }
      conteos.push(c);
    }
    const a = ajusteLogLog(tamanos, conteos);
    return { D: -a.pendiente, r2: a.r2, tamanos: tamanos, conteos: conteos, ordenada: a.ordenada };
  }

  function mascaraDeImagen(rgba, ancho, alto, umbral, objetoClaro) {
    const m = new Uint8Array(ancho * alto);
    for (let i = 0; i < ancho * alto; i++) {
      const g = (0.2126 * rgba[4 * i] + 0.7152 * rgba[4 * i + 1] + 0.0722 * rgba[4 * i + 2]) / 255;
      m[i] = objetoClaro ? (g >= umbral ? 1 : 0) : (g < umbral ? 1 : 0);
    }
    return m;
  }

  function masaRadio(mascara, ancho, cx, cy, radios) {
    const d = [];
    for (let i = 0; i < mascara.length; i++) if (mascara[i]) d.push(Math.hypot((i % ancho) - cx, Math.floor(i / ancho) - cy));
    const masas = radios.map(r => d.filter(v => v <= r).length);
    const a = ajusteLogLog(radios, masas);
    return { D: a.pendiente, r2: a.r2, radios: radios, masas: masas };
  }

  // ------------------------------------------------------------ caminatas
  function caminata(n, semilla) {
    const r = aleatorio(semilla || 1), p = new Float64Array(2 * (n + 1));
    let x = 0, y = 0;
    for (let k = 1; k <= n; k++) {
      const d = Math.floor(r() * 4);
      if (d === 0) x++; else if (d === 1) x--; else if (d === 2) y++; else y--;
      p[2 * k] = x; p[2 * k + 1] = y;
    }
    return p;
  }

  function vueloLevy(n, mu, semilla) {
    const r = aleatorio(semilla || 4), p = new Float64Array(2 * (n + 1));
    let x = 0, y = 0;
    for (let k = 1; k <= n; k++) {
      const l = Math.pow(1 - r(), -1 / mu), th = 2 * Math.PI * r();
      x += l * Math.cos(th); y += l * Math.sin(th);
      p[2 * k] = x; p[2 * k + 1] = y;
    }
    return p;
  }

  function msdBrowniano(nCam, nPasos, semilla) {
    const r = aleatorio(semilla || 2), msd = new Float64Array(nPasos);
    for (let c = 0; c < nCam; c++) {
      let x = 0, y = 0;
      for (let k = 0; k < nPasos; k++) {
        const d = Math.floor(r() * 4);
        if (d === 0) x++; else if (d === 1) x--; else if (d === 2) y++; else y--;
        msd[k] += x * x + y * y;
      }
    }
    const t = [], m = [];
    for (let k = 0; k < nPasos; k++) { t.push(k + 1); m.push(msd[k] / nCam); }
    return { t: t, msd: m };
  }

  function medianaLevy(nCam, nPasos, mu, semilla) {
    const r = aleatorio(semilla || 7), dist = [];
    for (let k = 0; k < nPasos; k++) dist.push(new Float64Array(nCam));
    for (let c = 0; c < nCam; c++) {
      let x = 0, y = 0;
      for (let k = 0; k < nPasos; k++) {
        const l = Math.pow(1 - r(), -1 / mu), th = 2 * Math.PI * r();
        x += l * Math.cos(th); y += l * Math.sin(th);
        dist[k][c] = Math.hypot(x, y);
      }
    }
    const t = [], med = [];
    for (let k = 0; k < nPasos; k++) { const s = Array.from(dist[k]).sort((a, b) => a - b); t.push(k + 1); med.push(s[Math.floor(nCam / 2)]); }
    return { t: t, mediana: med };
  }

  function ctrwMsd(nCam, tMax, alfa, semilla) {
    const r = aleatorio(semilla || 5), nT = 30, tiempos = [], msd = new Float64Array(nT);
    for (let k = 0; k < nT; k++) tiempos.push(10 * Math.pow(tMax / 10, k / (nT - 1)));
    for (let c = 0; c < nCam; c++) {
      let t = 0, x = 0, k = 0;
      while (k < nT) {
        t += Math.pow(1 - r(), -1 / alfa);
        while (k < nT && tiempos[k] < t) { msd[k] += x * x; k++; }
        x += r() < 0.5 ? 1 : -1;
      }
    }
    return { t: tiempos, msd: Array.from(msd, v => v / nCam) };
  }

  function exponente(t, y, tMin) {
    const xs = [], ys = [];
    for (let i = 0; i < t.length; i++) if (!tMin || t[i] >= tMin) { xs.push(t[i]); ys.push(y[i]); }
    return ajusteLogLog(xs, ys);
  }

  // ------------------------------------------------------------ DLA
  function DLA(lado, semilla) {
    this.lado = lado; this.c = Math.floor(lado / 2);
    this.g = new Uint8Array(lado * lado); this.orden = new Uint32Array(lado * lado);
    this.g[this.c * lado + this.c] = 1; this.n = 1; this.rMax = 1; this.r = aleatorio(semilla || 11);
  }
  DLA.prototype.anadir = function (k) {
    const L = this.lado, c = this.c, g = this.g, r = this.r;
    let hechas = 0;
    while (hechas < k) {
      const rNac = this.rMax + 5;
      if (rNac > c - 4) return false;
      const rMuerte = Math.min(3 * rNac + 20, c - 2);
      let a = r() * 2 * Math.PI;
      let x = c + Math.round(rNac * Math.cos(a)), y = c + Math.round(rNac * Math.sin(a));
      for (;;) {
        const d = Math.hypot(x - c, y - c);
        if (d > rMuerte) break;
        if (d > this.rMax + 3) {
          const s = d - this.rMax - 2; a = r() * 2 * Math.PI;
          x = Math.round(x + s * Math.cos(a)); y = Math.round(y + s * Math.sin(a)); continue;
        }
        const i = y * L + x;
        if (g[i + 1] || g[i - 1] || g[i + L] || g[i - L]) {
          g[i] = 1; this.n++; this.orden[i] = this.n; this.rMax = Math.max(this.rMax, d); hechas++; break;
        }
        const m = Math.floor(r() * 4);
        if (m === 0) x++; else if (m === 1) x--; else if (m === 2) y++; else y--;
      }
    }
    return true;
  };
  DLA.prototype.dimension = function () {
    let sx = 0, sy = 0, n = 0;
    for (let i = 0; i < this.g.length; i++) if (this.g[i]) { sx += i % this.lado; sy += Math.floor(i / this.lado); n++; }
    let s2 = 0;
    const mx = sx / n, my = sy / n;
    for (let i = 0; i < this.g.length; i++) if (this.g[i]) s2 += ((i % this.lado) - mx) ** 2 + (Math.floor(i / this.lado) - my) ** 2;
    const rg = Math.sqrt(s2 / n), radios = [];
    for (let k = 0; k < 8; k++) radios.push(4 * Math.pow(rg / 4, k / 7));
    const res = masaRadio(this.g, this.lado, this.c, this.c, radios);
    res.rg = rg;
    return res;
  };

  // ------------------------------------------------------------ percolación
  function redPercolacion(L, p, semilla) {
    const r = aleatorio(semilla || 21), m = new Uint8Array(L * L);
    for (let i = 0; i < L * L; i++) m[i] = r() < p ? 1 : 0;
    return m;
  }

  function cumulos(m, L) {
    const et = new Int32Array(L * L), tam = [0];
    let n = 0;
    const pila = [];
    for (let i = 0; i < L * L; i++) {
      if (!m[i] || et[i]) continue;
      n++; let t = 0; et[i] = n; pila.push(i);
      while (pila.length) {
        const k = pila.pop(); t++;
        const x = k % L, y = (k - x) / L;
        const v = [x > 0 ? k - 1 : -1, x < L - 1 ? k + 1 : -1, y > 0 ? k - L : -1, y < L - 1 ? k + L : -1];
        for (const j of v) if (j >= 0 && m[j] && !et[j]) { et[j] = n; pila.push(j); }
      }
      tam.push(t);
    }
    return { etiquetas: et, n: n, tamanos: tam };
  }

  function cruza(m, L) {
    const c = cumulos(m, L), arriba = new Set();
    for (let x = 0; x < L; x++) if (c.etiquetas[x]) arriba.add(c.etiquetas[x]);
    for (let x = 0; x < L; x++) if (arriba.has(c.etiquetas[(L - 1) * L + x])) return true;
    return false;
  }

  function probCruce(L, ps, muestras, semilla) {
    const r = aleatorio(semilla || 21);
    return ps.map(p => {
      let k = 0;
      for (let s = 0; s < muestras; s++) if (cruza(redPercolacion(L, p, Math.floor(r() * 4294967296)), L)) k++;
      return k / muestras;
    });
  }

  function umbralCruce(ps, P) {
    for (let k = 1; k < ps.length; k++) if (P[k] >= 0.5 && P[k - 1] < 0.5)
      return ps[k - 1] + (0.5 - P[k - 1]) * (ps[k] - ps[k - 1]) / (P[k] - P[k - 1]);
    return NaN;
  }

  // ------------------------------------------------------------ caos
  function bifurcacion(rMin, rMax, nR, transitorio, nPuntos) {
    const R = [], X = [];
    for (let i = 0; i < nR; i++) {
      const r = rMin + (rMax - rMin) * i / (nR - 1);
      let x = 0.2;
      for (let k = 0; k < transitorio; k++) x = r * x * (1 - x);
      for (let k = 0; k < nPuntos; k++) { x = r * x * (1 - x); R.push(r); X.push(x); }
    }
    return { r: R, x: X };
  }

  function lyapunovLogistico(r, n, transitorio) {
    let x = 0.2, s = 0;
    for (let k = 0; k < (transitorio || 1000); k++) x = r * x * (1 - x);
    const N = n || 100000;
    for (let k = 0; k < N; k++) { x = r * x * (1 - x); s += Math.log(Math.abs(r * (1 - 2 * x)) + 1e-300); }
    return s / N;
  }

  function campoLorenz(s) {
    const [x, y, z, a, b, c] = s;
    return [10 * (y - x), x * (28 - z) - y, x * y - (8 / 3) * z, 10 * (b - a), (28 - z) * a - b - x * c, y * a + x * b - (8 / 3) * c];
  }

  function rk4(s, dt) {
    const k1 = campoLorenz(s);
    const k2 = campoLorenz(s.map((v, i) => v + dt / 2 * k1[i]));
    const k3 = campoLorenz(s.map((v, i) => v + dt / 2 * k2[i]));
    const k4 = campoLorenz(s.map((v, i) => v + dt * k3[i]));
    return s.map((v, i) => v + dt / 6 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]));
  }

  function lorenz(n, dt, x0) {
    let s = [...(x0 || [1, 1, 1]), 0, 0, 0];
    const out = new Float64Array(3 * n);
    for (let k = 0; k < n; k++) { s = rk4(s, dt); out[3 * k] = s[0]; out[3 * k + 1] = s[1]; out[3 * k + 2] = s[2]; }
    return out;
  }

  function lyapunovLorenz(tTotal, dt) {
    let s = [1, 1, 1, 1, 0, 0], suma = 0;
    const trans = Math.round(20 / dt), pasos = Math.round(tTotal / dt);
    for (let k = 0; k < trans + pasos; k++) {
      s = rk4(s, dt);
      const nrm = Math.hypot(s[3], s[4], s[5]);
      s[3] /= nrm; s[4] /= nrm; s[5] /= nrm;
      if (k >= trans) suma += Math.log(nrm);
    }
    return suma / (pasos * dt);
  }

  // ------------------------------------------------------------ difusión fraccionaria (L1 implícito, Thomas)
  function gamma(z) {                       // aproximación de Lanczos
    const g = 7, c = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313, -176.61502916214059,
      12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
    if (z < 0.5) return Math.PI / (Math.sin(Math.PI * z) * gamma(1 - z));
    z -= 1;
    let x = c[0];
    for (let i = 1; i < g + 2; i++) x += c[i] / (z + i);
    const t = z + g + 0.5;
    return Math.sqrt(2 * Math.PI) * Math.pow(t, z + 0.5) * Math.exp(-t) * x;
  }

  function difusionFraccionaria(alfa, opciones) {
    const o = Object.assign({ K: 1, L: 12, nx: 481, T: 1, nt: 400, sigma0: 0.05 }, opciones || {});
    const x = [], dx = 2 * o.L / (o.nx - 1), h = o.T / o.nt;
    for (let i = 0; i < o.nx; i++) x.push(-o.L + i * dx);
    const c = 1 / (Math.pow(h, alfa) * gamma(2 - alfa));
    const b = [];
    for (let k = 0; k <= o.nt; k++) b.push(Math.pow(k + 1, 1 - alfa) - Math.pow(k, 1 - alfa));
    let u = x.map(v => Math.exp(-v * v / (2 * o.sigma0 * o.sigma0)));
    const s0 = u.reduce((a, v) => a + v, 0) * dx;
    u = u.map(v => v / s0);
    const r = o.K / (dx * dx), n = o.nx;
    const dif = [], t = [0], msd = [], perfiles = {};
    const momento = w => { let m = 0, s = 0; for (let i = 0; i < n; i++) { m += x[i] * x[i] * w[i]; s += w[i]; } return m / s - o.sigma0 * o.sigma0; };
    msd.push(momento(u));
    const marcas = new Set([Math.floor(o.nt / 8), Math.floor(o.nt / 4), Math.floor(o.nt / 2), o.nt]);
    for (let m = 1; m <= o.nt; m++) {
      const rhs = u.map(v => c * v);
      for (let j = 1; j < m; j++) { const d = dif[m - 1 - j]; for (let i = 0; i < n; i++) rhs[i] -= c * b[j] * d[i]; }
      rhs[0] = 0; rhs[n - 1] = 0;
      // Thomas: diagonal c + 2r, subdiagonal y superdiagonal −r; bordes de Dirichlet
      const cp = new Float64Array(n), dp = new Float64Array(n), un = new Float64Array(n);
      cp[0] = 0; dp[0] = 0;
      for (let i = 1; i < n - 1; i++) {
        const den = (c + 2 * r) - (-r) * cp[i - 1];
        cp[i] = -r / den; dp[i] = (rhs[i] - (-r) * dp[i - 1]) / den;
      }
      un[n - 1] = 0;
      for (let i = n - 2; i >= 1; i--) un[i] = dp[i] - cp[i] * un[i + 1];
      un[0] = 0;
      dif.push(Array.from(un, (v, i) => v - u[i]));
      u = Array.from(un);
      t.push(m * h); msd.push(momento(u));
      if (marcas.has(m)) perfiles[(m * h).toFixed(3)] = u.slice();
    }
    const tt = [], mm = [];
    for (let k = 0; k < t.length; k++) if (t[k] >= o.T / 10) { tt.push(t[k]); mm.push(msd[k]); }
    const a = ajusteLogLog(tt, mm);
    return { x: x, t: t, msd: msd, perfiles: perfiles, alfaAjustado: a.pendiente, coefAjustado: Math.exp(a.ordenada),
      coefTeorico: 2 * o.K / gamma(1 + alfa) };
  }

  // ------------------------------------------------------------ explicación sin clave
  function explicacionLocal(tema, resultado) {
    const l = ["Modo sin clave (no se ha usado ninguna IA). Resultado sobre «" + tema + "»:"];
    for (const [k, v] of Object.entries(resultado)) if (typeof v === "number") l.push("  - " + k + ": " + (Math.round(v * 1e4) / 1e4));
    if (resultado.D !== undefined) l.push("Una dimensión D entre 1 y 2 indica una curva que llena el plano más que una línea y menos que una superficie.");
    if (resultado.alfa !== undefined) {
      const a = resultado.alfa;
      l.push("Un exponente α ≈ " + a.toFixed(2) + " en ⟨x²⟩ ∝ t^α corresponde a " + (a < 0.95 ? "subdifusión" : a > 1.05 ? "superdifusión" : "difusión normal") + ".");
    }
    if (resultado.lyapunov !== undefined) l.push(resultado.lyapunov > 0 ? "λ > 0: sensibilidad a las condiciones iniciales (caos)." : "λ < 0: la órbita es estable (periódica).");
    l.push("Comprobaciones recomendadas:", "  1. Repite con otra semilla o resolución y mira cuánto cambia.",
      "  2. Ajusta solo en el tramo donde la gráfica log-log es recta.", "  3. Compara con el valor de referencia citado en el libro.");
    return l.join("\n");
  }

  return { aleatorio, ajusteLogLog, semejanza, cantor, koch, juegoDelCaos, sierpinskiMascara, escape, boxCounting, mascaraDeImagen,
    masaRadio, caminata, vueloLevy, msdBrowniano, medianaLevy, ctrwMsd, exponente, DLA, redPercolacion, cumulos, cruza, probCruce,
    umbralCruce, bifurcacion, lyapunovLogistico, lorenz, lyapunovLorenz, gamma, difusionFraccionaria, explicacionLocal };
});
