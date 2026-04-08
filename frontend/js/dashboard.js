/* ═══════════════════════════════════════════════════
   TaskFlow — dashboard.js
   Dashboard en tiempo real con Highcharts +
   sistema de menciones @usuario en comentarios
════════════════════════════════════════════════════ */

/* ── Highcharts CDN (cargado una vez) ── */
let _hcCargado = false;
async function _cargarHighcharts() {
  if (_hcCargado || window.Highcharts) {
    _hcCargado = true;
    return;
  }
  await new Promise((res, rej) => {
    const s = document.createElement("script");
    s.src =
      "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.2.0/highcharts.js";
    s.onload = res;
    s.onerror = rej;
    document.head.appendChild(s);
  });
  _hcCargado = true;
}

/* ── Paleta de colores adaptada al tema del app ── */
function _hcColores() {
  const esClaro =
    document.documentElement.getAttribute("data-tema") === "claro";
  return {
    bg: esClaro ? "#ffffff" : "#111113",
    plot: esClaro ? "#f1f1f3" : "#18181b",
    txt: esClaro ? "#52525b" : "#a1a1aa",
    txth: esClaro ? "#09090b" : "#fafafa",
    borde: esClaro ? "#d4d4d8" : "#3f3f46",
    serie: [
      "#6366f1",
      "#22c55e",
      "#f59e0b",
      "#ef4444",
      "#06b6d4",
      "#a855f7",
      "#ec4899",
    ],
  };
}

function _hcBase() {
  const c = _hcColores();
  return {
    chart: {
      backgroundColor: "transparent",
      style: { fontFamily: "Inter, sans-serif" },
    },
    title: { text: "" },
    credits: { enabled: false },
    legend: {
      itemStyle: { color: c.txt, fontSize: "11px", fontWeight: "400" },
      itemHoverStyle: { color: c.txth },
    },
    xAxis: {
      labels: { style: { color: c.txt, fontSize: "11px" } },
      lineColor: c.borde,
      tickColor: c.borde,
    },
    yAxis: {
      labels: { style: { color: c.txt, fontSize: "11px" } },
      gridLineColor: c.borde,
      title: { text: "" },
    },
    tooltip: {
      backgroundColor: c.bg,
      borderColor: c.borde,
      borderRadius: 8,
      style: { color: c.txth, fontSize: "12px" },
      shadow: false,
    },
    plotOptions: { series: { animation: { duration: 500 } } },
    colors: c.serie,
  };
}

/* Estado del dashboard */
let _dashProyId = null;
let _dashTimer = null;
let _dashMetricas = null;

/* ── FUNCIÓN PRINCIPAL ── */
async function cargarDashboard() {
  if (!S) return;

  // Fecha en el header
  const fechaEl = document.getElementById("dashFecha");
  if (fechaEl) {
    fechaEl.textContent = new Date().toLocaleDateString("es-CO", {
      weekday: "long",
      day: "2-digit",
      month: "long",
      year: "numeric",
    });
  }

  // Saludo personalizado
  const saludo = document.getElementById("dashSaludo");
  if (saludo) {
    const hora = new Date().getHours();
    const turno =
      hora < 12 ? "Buenos días" : hora < 18 ? "Buenas tardes" : "Buenas noches";
    saludo.textContent = `${turno}, ${S.usuario.nombre.split(" ")[0]}`;
  }

  // Cargar Highcharts y el selector en paralelo, luego métricas y proyectos en paralelo
  await _cargarHighcharts();
  await Promise.all([_poblarSelectorDash(), _cargarProyectosRecientes()]);
  await _cargarMetricasDash(_dashProyId);

  // Notificaciones (no PM)
  if (S.usuario.rol !== "PROJECT_MANAGER") {
    try {
      const ns = await api("GET", "/notificaciones/");
      const noLeidas = ns.filter((n) => !n.leida).length;
      const el = document.getElementById("stNotif");
      if (el) el.textContent = noLeidas;
      actualizarBadgeNotif(noLeidas);
    } catch (_) {}
  } else {
    const el = document.getElementById("stNotif");
    if (el) el.textContent = "—";
  }

  // Usuarios (solo ADMIN)
  if (S.usuario.rol === "ADMIN") {
    document.getElementById("statUsuariosWrap").style.display = "";
    try {
      const us = await api("GET", "/usuarios/");
      const el = document.getElementById("stUsers");
      if (el) el.textContent = us.length;
    } catch (_) {}
  }

  // Botón nuevo proyecto
  const acciones = document.getElementById("dashAcciones");
  if (
    acciones &&
    (S.usuario.rol === "PROJECT_MANAGER" || S.usuario.rol === "ADMIN")
  ) {
    acciones.innerHTML = `<button class="btn btn-primary btn-sm" onclick="abrirModal('mProy')">+ Nuevo proyecto</button>`;
  }

  // Auto-refresh cada 60 segundos
  clearInterval(_dashTimer);
  _dashTimer = setInterval(() => {
    if (
      document
        .getElementById("pantalla-dashboard")
        ?.classList.contains("activa")
    ) {
      _cargarMetricasDash(_dashProyId);
    }
  }, 60000);
}

function refrescarDashboard() {
  _cargarMetricasDash(_dashProyId);
  _cargarProyectosRecientes();
  toast("Dashboard actualizado");
}

async function _poblarSelectorDash() {
  const sel = document.getElementById("selDashProy");
  if (!sel) return;
  try {
    const ps = await api("GET", "/proyectos/");
    sel.innerHTML =
      '<option value="">— Todos los proyectos —</option>' +
      ps.map((p) => `<option value="${p.id}">${p.nombre}</option>`).join("");
  } catch (_) {}
}

async function actualizarDashboardProy(proyId) {
  _dashProyId = proyId || null;
  await _cargarMetricasDash(_dashProyId);
}

/* Helper: actualiza valor y subtítulo de una KPI card */
function _setKpi(id, valor, sub) {
  const el = document.getElementById(id);
  if (el) el.textContent = valor ?? "—";
  const subId = id + "Sub";
  const subEl = document.getElementById(subId);
  if (subEl && sub !== undefined) subEl.textContent = sub;
}

async function _cargarMetricasDash(proyId) {
  if (!S) return;
  try {
    const ps = await api("GET", "/proyectos/");

    if (proyId) {
      // Métricas de un proyecto específico
      _dashMetricas = await api("GET", `/proyectos/${proyId}/metricas`);
      const el = document.getElementById("stProy");
      if (el) el.textContent = ps.length;
      const elT = document.getElementById("stTareas");
      if (elT) elT.textContent = _dashMetricas.totalTareas;
      const elV = document.getElementById("stVencidas");
      if (elV) elV.textContent = _dashMetricas.tareasVencidas;
    } else {
      // Agregar métricas de todos los proyectos
      _setKpi(
        "stProy",
        ps.length,
        `${ps.length} proyecto${ps.length !== 1 ? "s" : ""}`,
      );
      let totalTareas = 0,
        totalVencidas = 0;
      const estadosAgregados = {},
        prioAgregada = {},
        tipoAgregado = {},
        usuariosAgregados = {};
      const velocidadAgg = {};

      // Cargar todas las métricas en paralelo en vez de en serie
      const todasMetricas = await Promise.all(
        ps.map((p) =>
          api("GET", `/proyectos/${p.id}/metricas`).catch(() => null),
        ),
      );
      todasMetricas.filter(Boolean).forEach((m) => {
        totalTareas += m.totalTareas || 0;
        totalVencidas += m.tareasVencidas || 0;
        Object.entries(m.tareasPorEstado || {}).forEach(
          ([k, v]) => (estadosAgregados[k] = (estadosAgregados[k] || 0) + v),
        );
        Object.entries(m.tareasPorPrioridad || {}).forEach(
          ([k, v]) => (prioAgregada[k] = (prioAgregada[k] || 0) + v),
        );
        Object.entries(m.tareasPorTipo || {}).forEach(
          ([k, v]) => (tipoAgregado[k] = (tipoAgregado[k] || 0) + v),
        );
        Object.entries(m.tareasPorUsuario || {}).forEach(
          ([k, v]) => (usuariosAgregados[k] = (usuariosAgregados[k] || 0) + v),
        );
        (m.velocidadPorSemana || []).forEach(
          (s) =>
            (velocidadAgg[s.semana] =
              (velocidadAgg[s.semana] || 0) + s.creadas),
        );
      });

      _dashMetricas = {
        totalTareas,
        tareasVencidas: totalVencidas,
        tareasPorEstado: estadosAgregados,
        tareasPorPrioridad: prioAgregada,
        tareasPorTipo: tipoAgregado,
        tareasPorUsuario: usuariosAgregados,
        velocidadPorSemana: Object.entries(velocidadAgg).map(([s, c]) => ({
          semana: s,
          creadas: c,
        })),
      };

      _setKpi("stTareas", totalTareas, `en ${ps.length} proyectos`);
      _setKpi(
        "stVencidas",
        totalVencidas,
        totalVencidas > 0 ? "requieren atención" : "al día ✓",
      );
    }

    _renderizarGraficos(_dashMetricas);
  } catch (e) {
    console.error("Dashboard error:", e.message);
  }
}

function _renderizarGraficos(m) {
  if (!window.Highcharts || !m) return;

  const c = _hcColores();

  /* 1. Donut — tareas por columna */
  const estadoEntradas = Object.entries(m.tareasPorEstado || {});
  Highcharts.chart("chartColumnas", {
    ..._hcBase(),
    chart: { ..._hcBase().chart, type: "pie" },
    plotOptions: {
      pie: {
        innerSize: "55%",
        borderWidth: 0,
        borderRadius: 4,
        dataLabels: {
          enabled: true,
          distance: 12,
          style: { fontSize: "11px", color: c.txt, fontWeight: "400" },
        },
        showInLegend: false,
      },
    },
    series: [
      {
        name: "Tareas",
        data: estadoEntradas.length
          ? estadoEntradas.map(([k, v]) => ({ name: k, y: v }))
          : [{ name: "Sin datos", y: 1, color: c.borde }],
      },
    ],
  });

  /* 2. Barras horizontales — prioridad */
  const prioColores = {
    BAJA: "#22c55e",
    MEDIA: "#f59e0b",
    ALTA: "#ef4444",
    URGENTE: "#a855f7",
  };
  const prioEntradas = Object.entries(m.tareasPorPrioridad || {});
  Highcharts.chart("chartPrioridad", {
    ..._hcBase(),
    chart: { ..._hcBase().chart, type: "bar" },
    xAxis: { categories: prioEntradas.map(([k]) => k), ..._hcBase().xAxis },
    yAxis: { ..._hcBase().yAxis, allowDecimals: false },
    plotOptions: {
      bar: { borderRadius: 4, borderWidth: 0, colorByPoint: true },
    },
    colors: prioEntradas.map(([k]) => prioColores[k] || "#6366f1"),
    legend: { enabled: false },
    series: [
      {
        name: "Tareas",
        data: prioEntradas.length ? prioEntradas.map(([, v]) => v) : [0],
      },
    ],
  });

  /* 3. Línea — velocidad semanal */
  const vel = m.velocidadPorSemana || [];
  Highcharts.chart("chartVelocidad", {
    ..._hcBase(),
    chart: { ..._hcBase().chart, type: "area" },
    xAxis: { categories: vel.map((s) => s.semana), ..._hcBase().xAxis },
    yAxis: { ..._hcBase().yAxis, allowDecimals: false },
    plotOptions: {
      area: {
        fillOpacity: 0.15,
        lineWidth: 2,
        borderRadius: 0,
        marker: { enabled: vel.length <= 8, radius: 4, symbol: "circle" },
      },
    },
    legend: { enabled: false },
    series: [
      { name: "Creadas", data: vel.map((s) => s.creadas), color: "#6366f1" },
    ],
  });

  /* 4. Columnas — por tipo */
  const tipoColores = {
    BUG: "#ef4444",
    FEATURE: "#06b6d4",
    TASK: "#a1a1aa",
    IMPROVEMENT: "#22c55e",
  };
  const tipoEntradas = Object.entries(m.tareasPorTipo || {});
  Highcharts.chart("chartTipo", {
    ..._hcBase(),
    chart: { ..._hcBase().chart, type: "column" },
    xAxis: { categories: tipoEntradas.map(([k]) => k), ..._hcBase().xAxis },
    yAxis: { ..._hcBase().yAxis, allowDecimals: false },
    plotOptions: {
      column: { borderRadius: 4, borderWidth: 0, colorByPoint: true },
    },
    colors: tipoEntradas.map(([k]) => tipoColores[k] || "#6366f1"),
    legend: { enabled: false },
    series: [
      {
        name: "Tareas",
        data: tipoEntradas.length ? tipoEntradas.map(([, v]) => v) : [0],
      },
    ],
  });

  /* 5. Barras horizontales — carga del equipo */
  const usuarios = Object.entries(m.tareasPorUsuario || {});
  const mapaU = _cacheUsuarios || {};
  const equipoData = usuarios
    .sort(([, a], [, b]) => b - a)
    .slice(0, 8)
    .map(([uid, cant]) => ({
      name: mapaU[uid]?.nombre || uid.slice(-6),
      y: cant,
    }));

  Highcharts.chart("chartEquipo", {
    ..._hcBase(),
    chart: { ..._hcBase().chart, type: "bar" },
    xAxis: { categories: equipoData.map((d) => d.name), ..._hcBase().xAxis },
    yAxis: { ..._hcBase().yAxis, allowDecimals: false },
    plotOptions: {
      bar: { borderRadius: 4, borderWidth: 0, colorByPoint: false },
    },
    colors: ["#6366f1"],
    legend: { enabled: false },
    series: [
      {
        name: "Tareas",
        data: equipoData.length ? equipoData.map((d) => d.y) : [0],
      },
    ],
  });
}

async function _cargarProyectosRecientes() {
  const cont = document.getElementById("dashProyectos");
  if (!cont) return;
  try {
    const ps = await api("GET", "/proyectos/");

    // Botón nuevo proyecto junto al título
    const accionesProy = document.getElementById("dashAccionesProy");
    if (
      accionesProy &&
      (S.usuario.rol === "PROJECT_MANAGER" || S.usuario.rol === "ADMIN")
    ) {
      accionesProy.innerHTML = `<button class="btn btn-primary btn-sm" onclick="abrirModal('mProy')"><i class="ph ph-plus"></i> Nuevo</button>`;
    }

    const iconoEstado = (e) =>
      ({
        PLANIFICADO: "ph-hourglass",
        EN_PROGRESO: "ph-play-circle",
        PAUSADO: "ph-pause-circle",
        COMPLETADO: "ph-check-circle",
        ARCHIVADO: "ph-archive",
      })[e] || "ph-folder";

    cont.innerHTML = ps.length
      ? ps
          .slice(0, 8)
          .map((p) => {
            const pct = Math.round(p.progreso || 0);
            return `
          <div class="proy-row">
            <div class="proy-ico">
              <i class="ph ${iconoEstado(p.estado)}"></i>
            </div>
            <div class="proy-info">
              <div class="proy-nombre">${p.nombre}</div>
              <div class="proy-meta">${p.descripcion || "Sin descripción"} · fin ${fFecha(p.fechaFinEstimada)}</div>
              <div class="proy-prog-wrap">
                <div class="prog" style="flex:1;height:4px"><div class="prog-bar" style="width:${pct}%"></div></div>
                <span class="proy-pct">${pct}%</span>
              </div>
            </div>
            ${badgeEstado(p.estado)}
            <div class="flex" style="gap:5px">
              <button class="btn btn-outline btn-xs" onclick="irTablero('${p.id}','${p.nombre}')">
                <i class="ph ph-kanban"></i> Tablero
              </button>
              ${
                S.usuario.rol !== "DEVELOPER"
                  ? `
                <button class="btn btn-ghost btn-xs" onclick="abrirInvitar('${p.id}')" title="Invitar miembro">
                  <i class="ph ph-user-plus"></i>
                </button>`
                  : ""
              }
            </div>
          </div>`;
          })
          .join("")
      : `<div class="vacío">
          <i class="ph ph-folder-open" style="font-size:36px;display:block;margin-bottom:10px;opacity:.25"></i>
          No tienes proyectos aún
         </div>`;
  } catch (e) {
    cont.innerHTML = `<div class="vacío">Error: ${e.message}</div>`;
  }
}

/* ══════════════════════════════════════════════════
   MENCIONES @usuario en comentarios
══════════════════════════════════════════════════ */

let _usuariosMencion = []; // cache de usuarios para autocomplete
let _tareaComentarioId = null;
let _paginaComentarios = 1;
const _LIMITE_COMENTARIOS = 15;

async function _cargarUsuariosMencion() {
  if (_usuariosMencion.length) return;
  try {
    const lista = await api("GET", "/usuarios/activos");
    _usuariosMencion = lista.map((u) => ({
      id: u.id,
      nombre: u.nombre,
      email: u.email,
      rol: u.rol,
      token: u.nombre.toLowerCase().replace(/\s+/g, ""),
    }));
  } catch (_) {}
}

/* Input con autocomplete de menciones */
function iniciarInputMenciones(inputId, sugerenciasId) {
  const input = document.getElementById(inputId);
  const sug = document.getElementById(sugerenciasId);
  if (!input || !sug) return;

  let _idx = -1;

  input.addEventListener("input", async () => {
    const val = input.value;
    const pos = input.selectionStart;
    // Buscar @ antes del cursor
    const antes = val.slice(0, pos);
    const match = antes.match(/@([\w\.]*)$/);
    if (!match) {
      sug.classList.remove("visible");
      return;
    }

    await _cargarUsuariosMencion();
    const query = match[1].toLowerCase();
    const filtrados = _usuariosMencion
      .filter(
        (u) => u.token.includes(query) || u.email.toLowerCase().includes(query),
      )
      .slice(0, 6);

    if (!filtrados.length) {
      sug.classList.remove("visible");
      return;
    }

    sug.innerHTML = filtrados
      .map(
        (u, i) => `
      <div class="sug-item" data-i="${i}" data-nombre="${u.nombre}" onclick="_insertarMencion('${inputId}','${sugerenciasId}','${u.nombre}')">
        <div class="avatar avatar-sm">${inic(u.nombre)}</div>
        <div>
          <div style="font-size:12px;font-weight:500">${u.nombre}</div>
          <div class="txt3">${u.email}</div>
        </div>
      </div>`,
      )
      .join("");
    sug.classList.add("visible");
    _idx = -1;
  });

  input.addEventListener("keydown", (e) => {
    if (!sug.classList.contains("visible")) return;
    const items = sug.querySelectorAll(".sug-item");
    if (e.key === "ArrowDown") {
      e.preventDefault();
      _idx = Math.min(_idx + 1, items.length - 1);
      _resaltarSug(items, _idx);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      _idx = Math.max(_idx - 1, 0);
      _resaltarSug(items, _idx);
    } else if (e.key === "Enter" && _idx >= 0) {
      e.preventDefault();
      const nombre = items[_idx]?.dataset.nombre;
      if (nombre) _insertarMencion(inputId, sugerenciasId, nombre);
    } else if (e.key === "Escape") {
      sug.classList.remove("visible");
    }
  });

  document.addEventListener("click", (e) => {
    if (!sug.contains(e.target) && e.target !== input)
      sug.classList.remove("visible");
  });
}

function _resaltarSug(items, idx) {
  items.forEach((it, i) => it.classList.toggle("activo", i === idx));
}

function _insertarMencion(inputId, sugerenciasId, nombre) {
  const input = document.getElementById(inputId);
  const sug = document.getElementById(sugerenciasId);
  if (!input) return;
  const val = input.value;
  const pos = input.selectionStart;
  const antes = val.slice(0, pos);
  // Reemplazar @parcial por @nombre completo + espacio
  const nuevo = antes.replace(/@[\w\.]*$/, `@${nombre} `) + val.slice(pos);
  input.value = nuevo;
  input.focus();
  sug.classList.remove("visible");
}

/* ── PANEL DE COMENTARIOS ── */
async function abrirPanelComentarios(tareaId, tituloTarea) {
  _tareaComentarioId = tareaId;
  _paginaComentarios = 1;

  // Crear o reusar modal de comentarios
  let modal = document.getElementById("mComentarios");
  if (!modal) {
    modal = document.createElement("div");
    modal.className = "overlay";
    modal.id = "mComentarios";
    modal.innerHTML = `
      <div class="modal" style="width:580px;max-height:80vh;display:flex;flex-direction:column">
        <div class="flex-between" style="margin-bottom:16px">
          <div class="modal-t" style="margin-bottom:0" id="mComTitulo">Comentarios</div>
          <button class="btn btn-ghost btn-xs" onclick="cerrarModal('mComentarios')">✕</button>
        </div>
        <div id="listaComentarios" style="flex:1;overflow-y:auto;min-height:120px" class="vacío">Cargando...</div>
        <div id="pagComentarios" style="margin-top:4px"></div>
        <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--borde)">
          <div class="input-menciones-wrap">
            <textarea class="ftextarea" id="nuevoComentario"
              placeholder="Escribe un comentario... usa @nombre para mencionar"
              style="min-height:68px;resize:none"></textarea>
            <div class="sugerencias-menciones" id="sugComentario"></div>
          </div>
          <div class="flex-between" style="margin-top:8px">
            <span class="txt3" style="font-size:10px">@ para mencionar usuarios</span>
            <button class="btn btn-primary btn-sm" onclick="enviarComentario()">Enviar</button>
          </div>
        </div>
      </div>`;
    document.body.appendChild(modal);
    modal.addEventListener("click", (e) => {
      if (e.target === modal) cerrarModal("mComentarios");
    });
  }

  document.getElementById("mComTitulo").textContent =
    `Comentarios · ${tituloTarea}`;
  abrirModal("mComentarios");
  await _cargarUsuariosMencion();
  iniciarInputMenciones("nuevoComentario", "sugComentario");
  await _cargarComentariosPaginados(tareaId, 1);
}

async function _cargarComentariosPaginados(tareaId, pagina) {
  const lista = document.getElementById("listaComentarios");
  const pagEl = document.getElementById("pagComentarios");
  if (!lista) return;
  lista.innerHTML = '<span class="spinner"></span>';
  try {
    const res = await api(
      "GET",
      `/tareas/${tareaId}/comentarios?pagina=${pagina}&limite=${_LIMITE_COMENTARIOS}`,
    );
    _paginaComentarios = pagina;
    const comentarios = res.datos || res; // compatibilidad si backend aún devuelve array

    if (!comentarios.length) {
      lista.innerHTML =
        '<div class="vacío">Sin comentarios aún. ¡Sé el primero!</div>';
    } else {
      const mapaU = await _obtenerMapaUsuarios();
      lista.innerHTML = comentarios
        .map((c) => {
          const u = mapaU[c.autorId];
          const nombre = u ? u.nombre : `ID:${c.autorId.slice(-6)}`;
          const av = `<div class="avatar avatar-sm">${inic(nombre)}</div>`;
          const html = c.contenidoHtml || c.contenido;
          return `<div class="comentario-item">
          <div class="comentario-header">
            ${av}
            <span class="comentario-autor">${nombre}</span>
            <span class="comentario-fecha">${fFecha(c.creadoEn)}</span>
          </div>
          <div class="comentario-cuerpo">${html}</div>
        </div>`;
        })
        .join("");
    }

    // Paginación
    if (res.totalPaginas > 1) {
      pagEl.innerHTML = _renderizarPaginacion(
        res.pagina,
        res.totalPaginas,
        (p) => _cargarComentariosPaginados(tareaId, p),
      );
    } else {
      pagEl.innerHTML = "";
    }
  } catch (e) {
    lista.innerHTML = `<div class="vacío">Error: ${e.message}</div>`;
  }
}

async function enviarComentario() {
  const input = document.getElementById("nuevoComentario");
  if (!input) return;
  const texto = input.value.trim();
  if (!texto || !_tareaComentarioId) return;
  const btn = document.querySelector("#mComentarios .btn-primary");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "...";
  }
  try {
    await api("POST", `/tareas/${_tareaComentarioId}/comentarios`, {
      contenido: texto,
    });
    input.value = "";
    await _cargarComentariosPaginados(_tareaComentarioId, _paginaComentarios);
    toast("Comentario enviado");
  } catch (e) {
    toast(e.message, "err");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Enviar";
    }
  }
}

/* ══════════════════════════════════════════════════
   PAGINACIÓN GENÉRICA (reutilizable)
══════════════════════════════════════════════════ */
function _renderizarPaginacion(paginaActual, totalPaginas, onCambio) {
  if (totalPaginas <= 1) return "";
  const btns = [];

  // Anterior
  btns.push(`<button class="pag-btn" ${paginaActual <= 1 ? "disabled" : ""}
    onclick="(${onCambio.toString()})(${paginaActual - 1})">‹</button>`);

  // Páginas cercanas
  const inicio = Math.max(1, paginaActual - 2);
  const fin = Math.min(totalPaginas, paginaActual + 2);
  if (inicio > 1)
    btns.push(
      `<button class="pag-btn" onclick="(${onCambio.toString()})(1)">1</button>`,
    );
  if (inicio > 2) btns.push(`<span class="pag-info">…</span>`);
  for (let i = inicio; i <= fin; i++) {
    btns.push(`<button class="pag-btn ${i === paginaActual ? "activo" : ""}"
      onclick="(${onCambio.toString()})(${i})">${i}</button>`);
  }
  if (fin < totalPaginas - 1) btns.push(`<span class="pag-info">…</span>`);
  if (fin < totalPaginas)
    btns.push(
      `<button class="pag-btn" onclick="(${onCambio.toString()})(${totalPaginas})">${totalPaginas}</button>`,
    );

  // Siguiente
  btns.push(`<button class="pag-btn" ${paginaActual >= totalPaginas ? "disabled" : ""}
    onclick="(${onCambio.toString()})(${paginaActual + 1})">›</button>`);

  return `<div class="paginacion">${btns.join("")}
    <span class="pag-info">Pág ${paginaActual} / ${totalPaginas}</span>
  </div>`;
}

/* Paginación para la vista de Tareas (tabla) */
let _paginaTareas = 1;
const _LIMITE_TAREAS = 20;

async function cargarTareasPaginadas(proyId, pagina) {
  if (!proyId) return;
  proyActualId = proyId;
  _paginaTareas = pagina || 1;

  // Cargar columnas del tablero para el modal de nueva tarea
  try {
    const tableros = await api("GET", `/proyectos/${proyId}/tableros`);
    colsActuales = tableros[0]?.columnas || [];
  } catch (_) {
    colsActuales = [];
  }

  try {
    const todos = await api("GET", "/usuarios/activos");
    miembrosActuales = todos
      .filter((u) => u.rol === "DEVELOPER")
      .map((u) => ({ id: u.id, nombre: u.nombre, email: u.email, rol: u.rol }));
  } catch (_) {
    miembrosActuales = [];
  }

  const tb = document.getElementById("tbTareas");
  const pagEl = document.getElementById("pagTareas");
  if (tb)
    tb.innerHTML =
      '<tr><td colspan="6" class="vacío"><span class="spinner"></span></td></tr>';

  try {
    const res = await api(
      "GET",
      `/proyectos/${proyId}/tareas?pagina=${_paginaTareas}&limite=${_LIMITE_TAREAS}`,
    );
    const ts = res.datos || res;

    if (!ts.length) {
      tb.innerHTML =
        '<tr><td colspan="6" class="vacío">Sin tareas en este proyecto</td></tr>';
      if (pagEl) pagEl.innerHTML = "";
      return;
    }

    tb.innerHTML = ts
      .map((t) => {
        const resps = (t.responsables || [])
          .map((id) => {
            const m = miembrosActuales.find((m) => m.id === id);
            return `<div class="avatar avatar-sm" title="${m?.nombre || id}">${inic(m?.nombre || "?")}</div>`;
          })
          .join("");
        return `<tr>
        <td style="color:var(--txt);font-weight:500;cursor:pointer" onclick="abrirPanelComentarios('${t.id}','${t.titulo.replace(/'/g, "\\'")}')">
          ${t.titulo}
        </td>
        <td>${badgeTipo(t.tipo)}</td>
        <td>${badgePrio(t.prioridad)}</td>
        <td><div class="avatar-group">${resps || '<span class="txt3">—</span>'}</div></td>
        <td>${t.estaVencida ? '<span class="badge br">Vencida</span>' : '<span class="badge bg">Activa</span>'}</td>
        <td><div class="flex" style="gap:4px">
          <button class="btn btn-outline btn-xs" onclick="abrirPanelComentarios('${t.id}','${t.titulo.replace(/'/g, "\\'")}')">💬</button>
          <button class="btn btn-outline btn-xs" onclick="abrirPanelSubtareas('${t.id}','${t.titulo.replace(/'/g, "\\'")}')">📋</button>
          <button class="btn btn-outline btn-xs" onclick="abrirAsignar('${t.id}')">Asignar</button>
          <button class="btn btn-outline btn-xs" onclick="clonarTarea('${t.id}')">Clonar</button>
          <button class="btn btn-red btn-xs" onclick="eliminarTarea('${t.id}')">✕</button>
        </div></td>
      </tr>`;
      })
      .join("");

    // Paginación de tareas
    if (pagEl && res.totalPaginas > 1) {
      pagEl.innerHTML = _renderizarPaginacion(
        res.pagina,
        res.totalPaginas,
        (p) => cargarTareasPaginadas(proyId, p),
      );
    } else if (pagEl) {
      pagEl.innerHTML = "";
    }
  } catch (e) {
    if (tb)
      tb.innerHTML = `<tr><td colspan="6" class="vacío">Error: ${e.message}</td></tr>`;
  }
}
