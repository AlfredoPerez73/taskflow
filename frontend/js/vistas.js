/* ═══════════════════════════════════════════════════
   TaskFlow — vistas.js
   Lógica de cada pantalla: proyectos, tareas, usuarios,
   reportes, historial, notificaciones, perfil
════════════════════════════════════════════════════ */

/* ══════════ DASHBOARD ══════════ */
/* cargarDashboard movido a dashboard.js */

/* ══════════ PROYECTOS ══════════ */
async function cargarProyectos() {
  if (!S) return;
  const acciones = document.getElementById("proyAcciones");
  if (S.usuario.rol === "PROJECT_MANAGER" || S.usuario.rol === "ADMIN") {
    acciones.innerHTML = `<button class="btn btn-primary btn-sm" onclick="abrirModal('mProy')"><i class="ph ph-plus"></i> Nuevo proyecto</button>`;
  }
  document.getElementById("listaProyectos").innerHTML = "Cargando...";
  try {
    const ps = await api("GET", "/proyectos/");
    if (!ps.length) {
      document.getElementById("listaProyectos").innerHTML =
        '<div class="vacío">No hay proyectos</div>';
      return;
    }
    document.getElementById("listaProyectos").innerHTML = ps
      .map(
        (p) => `
      <div class="prow">
        <div>
          <div class="prow-name">${p.nombre}</div>
          <div class="prow-desc">${p.descripcion || "Sin descripción"} · Fin: ${fFecha(p.fechaFinEstimada)}</div>
          <div class="prow-prog"><div class="prog"><div class="prog-bar" style="width:${p.progreso}%"></div></div></div>
        </div>
        ${badgeEstado(p.estado)}
        <div class="flex" style="gap:5px">
          <button class="btn btn-outline btn-xs" onclick="irTablero('${p.id}','${p.nombre}')"><i class='ph ph-kanban'></i> Tablero</button>
          ${
            S.usuario.rol !== "DEVELOPER"
              ? `
            <button class="btn btn-outline btn-xs" onclick="abrirInvitar('${p.id}')"><i class='ph ph-user-plus'></i> Invitar</button>
            <button class="btn btn-outline btn-xs" onclick="clonarProyecto('${p.id}')"><i class='ph ph-copy'></i> Clonar</button>
            ${!p.estaArchivado ? `<button class="btn btn-ghost btn-xs" onclick="archivarProyecto('${p.id}')">Archivar</button>` : ""}
          `
              : ""
          }
        </div>
      </div>`,
      )
      .join("");
  } catch (e) {
    toast(e.message, "err");
  }
}

async function crearProyecto() {
  document.getElementById("pError").textContent = "";
  try {
    await api("POST", "/proyectos/", {
      nombre: document.getElementById("pNom").value,
      descripcion: document.getElementById("pDesc").value || null,
      fechaInicio: document.getElementById("pFI").value,
      fechaFinEstimada: document.getElementById("pFF").value,
    });
    cerrarModal("mProy");
    toast("Proyecto creado");
    cargarProyectos();
  } catch (e) {
    document.getElementById("pError").textContent = e.message;
  }
}

async function archivarProyecto(id) {
  if (!confirm("¿Archivar este proyecto?")) return;
  try {
    await api("POST", `/proyectos/${id}/archivar`);
    toast("Proyecto archivado");
    cargarProyectos();
  } catch (e) {
    toast(e.message, "err");
  }
}

async function clonarProyecto(id) {
  try {
    await api("POST", `/proyectos/${id}/clonar`);
    toast("Proyecto clonado");
    cargarProyectos();
  } catch (e) {
    toast(e.message, "err");
  }
}

function abrirInvitar(proyId) {
  document.getElementById("invitarPrId").value = proyId;
  document.getElementById("invEmail").value = "";
  document.getElementById("invError").textContent = "";
  abrirModal("mInvitar");
}

async function invitarMiembro() {
  document.getElementById("invError").textContent = "";
  const proyId = document.getElementById("invitarPrId").value;
  try {
    const r = await api("POST", `/proyectos/${proyId}/invitar`, {
      email: document.getElementById("invEmail").value,
      rolEnProyecto: "DEVELOPER",
    });
    cerrarModal("mInvitar");
    toast(r.mensaje);
  } catch (e) {
    document.getElementById("invError").textContent = e.message;
  }
}

/* ── Caché de usuarios activos con TTL de 5 minutos ── */
let _cacheUsuariosActivos = null;
let _cacheTsUsuariosActivos = 0;
const _TTL_USUARIOS = 5 * 60 * 1000; // 5 minutos

async function _getUsuariosActivos(forzar = false) {
  const ahora = Date.now();
  if (
    !forzar &&
    _cacheUsuariosActivos &&
    ahora - _cacheTsUsuariosActivos < _TTL_USUARIOS
  ) {
    return _cacheUsuariosActivos;
  }
  const todos = await api("GET", "/usuarios/activos");
  _cacheUsuariosActivos = todos
    .filter((u) => u.rol === "DEVELOPER")
    .map((u) => ({ id: u.id, nombre: u.nombre, email: u.email, rol: u.rol }));
  _cacheTsUsuariosActivos = ahora;
  return _cacheUsuariosActivos;
}

/* Invalidar caché al crear/desactivar usuario */
function _invalidarCacheUsuarios() {
  _cacheUsuariosActivos = null;
  _cacheTsUsuariosActivos = 0;
}
/* ══════════ TAREAS ══════════ */
async function abrirModalTarea() {
  if (!proyActualId) {
    toast("Primero selecciona un proyecto", "err");
    return;
  }
  // Abrir el modal INMEDIATAMENTE sin esperar la API
  document.getElementById("tCol").innerHTML = colsActuales
    .map((c) => `<option value="${c.id}">${c.nombre}</option>`)
    .join("");
  document.getElementById("tError").textContent = "";
  document.getElementById("tTit").value = "";
  document.getElementById("tDesc").value = "";
  abrirModal("mTarea");
  // Cargar responsables en segundo plano (el modal ya está visible)
  try {
    miembrosActuales = await _getUsuariosActivos();
    renderRespLista("respLista", []);
  } catch (_) {
    renderRespLista("respLista", []);
  }
}

function abrirModalTareaCol(colId) {
  abrirModalTarea();
  setTimeout(() => {
    const s = document.getElementById("tCol");
    if (s) s.value = colId;
  }, 50);
}

function renderRespLista(contenedorId, seleccionados) {
  const c = document.getElementById(contenedorId);
  if (!miembrosActuales.length) {
    c.innerHTML = '<span class="txt3">Sin developers disponibles</span>';
    return;
  }
  c.innerHTML = miembrosActuales
    .map(
      (m) => `
    <div class="resp-chip ${seleccionados.includes(m.id) ? "sel" : ""}"
      onclick="toggleResp(this,'${m.id}','${contenedorId}')" data-id="${m.id}">
      <div class="avatar avatar-sm">${inic(m.nombre)}</div>
      ${m.nombre}
    </div>`,
    )
    .join("");
}

function toggleResp(el) {
  el.classList.toggle("sel");
}

function getSeleccionados(contenedorId) {
  return [...document.querySelectorAll(`#${contenedorId} .resp-chip.sel`)].map(
    (c) => c.dataset.id,
  );
}

async function crearTarea() {
  document.getElementById("tError").textContent = "";
  const colId = document.getElementById("tCol").value;
  if (!colId) {
    document.getElementById("tError").textContent = "Selecciona una columna";
    return;
  }
  try {
    await api("POST", "/tareas", {
      titulo: document.getElementById("tTit").value,
      descripcion: document.getElementById("tDesc").value || null,
      tipo: document.getElementById("tTipo").value,
      prioridad: document.getElementById("tPrio").value,
      columnaId: colId,
      proyectoId: proyActualId,
      fechaVencimiento: document.getElementById("tFV").value || null,
      responsables: getSeleccionados("respLista"),
      etiquetas: [],
    });
    cerrarModal("mTarea");
    toast("Tarea creada");
    // Actualizar vista según la pantalla activa
    const pantallaActiva = document.querySelector(".pantalla.activa");
    if (pantallaActiva?.id === "pantalla-tareas") {
      cargarTareasPaginadas(proyActualId, _paginaTareas || 1);
    } else {
      cargarTablero(proyActualId);
    }
  } catch (e) {
    document.getElementById("tError").textContent = e.message;
  }
}

/* cargarTareas reemplazada por cargarTareasPaginadas en dashboard.js */

async function abrirAsignar(tareaId) {
  document.getElementById("asignarTareaId").value = tareaId;
  if (!proyActualId) {
    toast("Primero carga un proyecto", "err");
    return;
  }
  // Abrir modal inmediatamente con skeleton
  document.getElementById("asignarLista").innerHTML =
    '<span class="spinner"></span>';
  abrirModal("mAsignar");
  // Cargar usuarios y tarea en paralelo
  try {
    const [devs, tarea] = await Promise.all([
      _getUsuariosActivos(),
      api("GET", `/tareas/${tareaId}`),
    ]);
    miembrosActuales = devs;
    renderRespLista("asignarLista", tarea.responsables || []);
  } catch (e) {
    cerrarModal("mAsignar");
    toast(e.message, "err");
  }
}

async function guardarAsignacion() {
  const tareaId = document.getElementById("asignarTareaId").value;
  const sel = getSeleccionados("asignarLista");
  try {
    await api("PUT", `/tareas/${tareaId}/responsables`, { responsables: sel });
    cerrarModal("mAsignar");
    toast("Responsables asignados");
    if (proyActualId) cargarTablero(proyActualId);
  } catch (e) {
    toast(e.message, "err");
  }
}

async function clonarTarea(id) {
  try {
    await api("POST", `/tareas/${id}/clonar`);
    toast("Tarea clonada");
    if (proyActualId) cargarTablero(proyActualId);
  } catch (e) {
    toast(e.message, "err");
  }
}

async function eliminarTarea(id) {
  if (!confirm("¿Eliminar esta tarea?")) return;
  try {
    await api("DELETE", `/tareas/${id}`);
    toast("Tarea eliminada");
    if (proyActualId) cargarTablero(proyActualId);
  } catch (e) {
    toast(e.message, "err");
  }
}

/* ══════════ USUARIOS ══════════ */
async function cargarUsuarios() {
  if (S?.usuario?.rol !== "ADMIN") {
    document.getElementById("tbUsuarios").innerHTML =
      '<tr><td colspan="6" class="vacío">Acceso restringido a Administradores</td></tr>';
    return;
  }
  try {
    const us = await api("GET", "/usuarios/");
    document.getElementById("tbUsuarios").innerHTML = us
      .map(
        (u) => `<tr>
      <td><div class="flex" style="gap:8px">
        <div class="avatar avatar-sm">${inic(u.nombre)}</div>${u.nombre}
      </div></td>
      <td class="txt2">${u.email}</td>
      <td>${badgeRol(u.rol)}</td>
      <td class="txt3">${fFecha(u.ultimoAcceso)}</td>
      <td><span class="badge ${u.estaActivo ? "bg" : "br"}">${u.estaActivo ? "Activo" : "Inactivo"}</span></td>
      <td>${
        u.estaActivo && u.id !== S.usuario.id
          ? `<button class="btn btn-red btn-xs" onclick="desactivarUsuario('${u.id}')">Desactivar</button>`
          : ""
      }</td>
    </tr>`,
      )
      .join("");
  } catch (e) {
    toast(e.message, "err");
  }
}

async function desactivarUsuario(id) {
  if (!confirm("¿Desactivar este usuario?")) return;
  try {
    await api("PUT", `/usuarios/${id}/desactivar`);
    toast("Usuario desactivado");
    cargarUsuarios();
  } catch (e) {
    toast(e.message, "err");
  }
}

/* ══════════ REPORTES ══════════ */
async function cargarReporte(proyId) {
  if (!proyId) {
    ["rTotal", "rVenc", "rProg"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.textContent = "—";
    });
    const dist = document.getElementById("rDist");
    if (dist)
      dist.innerHTML = '<div class="vacío">Selecciona un proyecto</div>';
    return;
  }
  const elems = ["rTotal", "rVenc", "rProg", "rDist"];
  elems.forEach((id) => {
    const el = document.getElementById(id);
    if (el && id !== "rDist") el.textContent = "—";
    if (el && id === "rDist")
      el.innerHTML = '<div class="vacío">Cargando...</div>';
  });
  try {
    const m = await api("GET", `/proyectos/${proyId}/metricas`);
    document.getElementById("rTotal").textContent = m.totalTareas ?? "0";
    document.getElementById("rVenc").textContent = m.tareasVencidas ?? "0";
    document.getElementById("rProg").textContent = `${m.progreso ?? 0}%`;
    const dist = Object.entries(m.tareasPorEstado || {});
    const maxD = Math.max(...dist.map(([, v]) => v), 1);
    document.getElementById("rDist").innerHTML = dist.length
      ? dist
          .map(([col, cant]) => {
            const pctD = Math.round((cant / maxD) * 100);
            return `
          <div class="metrica-row">
            <span class="metrica-label">${col}</span>
            <div class="metrica-bar-track">
              <div class="metrica-bar-fill" style="width:${pctD}%"></div>
            </div>
            <span class="metrica-cant">${cant}</span>
          </div>`;
          })
          .join("")
      : '<div class="vacío">Sin tareas aún</div>';
    // Recargar panel activo si corresponde
    const panelEquipo = document.getElementById("rpanel-equipo");
    if (panelEquipo?.classList.contains("activo"))
      cargarEstadisticasEquipo(proyId);
    const panelSprint = document.getElementById("rpanel-sprint");
    if (panelSprint?.classList.contains("activo")) {
      document.getElementById("contenidoSprint").innerHTML =
        '<div class="vacío">Ingresa el nombre del sprint y haz clic en Generar</div>';
    }
  } catch (e) {
    toast("Error cargando métricas: " + e.message, "err");
    document.getElementById("rDist").innerHTML =
      `<div class="vacío">Error: ${e.message}</div>`;
  }
}

/* ══════════ HISTORIAL ══════════ */
let historialUltimoCambio = null;

function cambiarTabHist(nombre, btn) {
  // Limitar a los tabs/panels dentro del historial para no afectar los de reportes
  const pantalla = document.getElementById("pantalla-historial");
  if (!pantalla) return;
  pantalla
    .querySelectorAll(".htab")
    .forEach((t) => t.classList.remove("activo"));
  pantalla
    .querySelectorAll(".hpanel")
    .forEach((p) => p.classList.remove("activo"));
  btn.classList.add("activo");
  pantalla.querySelector(`#hpanel-${nombre}`)?.classList.add("activo");
  if (nombre === "completadas") cargarTareasCompletadas();
}

// Cache de usuarios para resolución de nombres
let _cacheUsuarios = null;
async function _obtenerMapaUsuarios() {
  if (_cacheUsuarios) return _cacheUsuarios;
  try {
    // /usuarios/activos es accesible por todos los roles (no solo ADMIN)
    const lista = await api("GET", "/usuarios/activos");
    _cacheUsuarios = {};
    lista.forEach((u) => {
      _cacheUsuarios[u.id] = u;
    });
  } catch (_) {
    _cacheUsuarios = {};
  }
  return _cacheUsuarios;
}
function _nombreUsuario(mapaU, usuarioId) {
  const u = mapaU[usuarioId];
  return u ? u.nombre : `ID:${usuarioId.slice(-6)}`;
}

async function cargarHistorial(proyId) {
  if (!proyId) {
    const el = document.getElementById("listaHist");
    if (el) el.innerHTML = '<div class="vacío">Selecciona un proyecto</div>';
    return;
  }
  document.getElementById("listaHist").innerHTML =
    '<span class="spinner"></span>';
  try {
    const res = await api("GET", `/proyectos/${proyId}/auditoria?limite=100`);
    // Soportar tanto array plano como respuesta paginada
    const rs = Array.isArray(res) ? res : res.datos || [];
    const mapaU = await _obtenerMapaUsuarios();

    if (!rs.length) {
      document.getElementById("listaHist").innerHTML =
        '<div class="vacío">Sin registros de auditoría</div>';
      return;
    }
    document.getElementById("listaHist").innerHTML = `<div class="timeline">${rs
      .filter((r) => r && r.usuarioId)
      .map((r, i) => {
        const nombre = _nombreUsuario(mapaU, r.usuarioId);
        const u = mapaU[r.usuarioId];
        const av = u
          ? `<div class="avatar avatar-sm" style="display:inline-flex;vertical-align:middle;margin-right:4px">${inic(u.nombre)}</div>`
          : "";
        return `
        <div class="tl-item ${i === 0 ? "reciente" : ""}">
          <div class="tl-accion"><strong>${r.accion || "—"}</strong> en ${r.tipoEntidad || "—"}</div>
          <div class="tl-meta">${av}${nombre} · ${fFecha(r.marca)}</div>
        </div>`;
      })
      .join("")}</div>`;
  } catch (e) {
    document.getElementById("listaHist").innerHTML =
      `<div class="vacío">Error: ${e.message}</div>`;
  }
}

async function cargarHistorialTarea() {
  const raw = document.getElementById("histTareaId").value.trim();
  if (!raw) {
    toast("Ingresa un ID de tarea", "err");
    return;
  }
  document.getElementById("listaHistTarea").innerHTML =
    '<span class="spinner"></span>';
  document.getElementById("undoZona").style.display = "none";
  try {
    let tareaId = raw;
    if (proyActualId && raw.length <= 6) {
      const tareas = await api("GET", `/proyectos/${proyActualId}/tareas`);
      const encontrada = tareas.find((t) => t.id.endsWith(raw));
      if (encontrada) tareaId = encontrada.id;
    }
    const rs = await api("GET", `/tareas/${tareaId}/historial`);
    if (!rs.length) {
      document.getElementById("listaHistTarea").innerHTML =
        '<div class="vacío">Sin historial para esta tarea</div>';
      return;
    }
    historialUltimoCambio = rs[0];
    const mapaU2 = await _obtenerMapaUsuarios();
    document.getElementById("listaHistTarea").innerHTML =
      `<div class="timeline">${rs
        .map((r, i) => {
          const nombre = _nombreUsuario(mapaU2, r.usuarioId);
          const u2 = mapaU2[r.usuarioId];
          const av = u2
            ? `<div class="avatar avatar-sm" style="display:inline-flex;vertical-align:middle;margin-right:4px">${inic(u2.nombre)}</div>`
            : "";
          return `
        <div class="tl-item ${i === 0 ? "reciente" : ""}">
          <div class="tl-accion"><strong>${r.accion}</strong> en ${r.tipoEntidad}</div>
          <div class="tl-meta">${av}${nombre} · ${fFecha(r.marca)}</div>
        </div>`;
        })
        .join("")}</div>`;
    if (historialUltimoCambio) {
      document.getElementById("undoZona").style.display = "";
      document.getElementById("undoDetalle").textContent =
        historialUltimoCambio.valorAnterior
          ? `Revertir: ${historialUltimoCambio.accion} (${fFecha(historialUltimoCambio.marca)})`
          : "No hay cambio anterior para revertir";
    }
  } catch (e) {
    document.getElementById("listaHistTarea").innerHTML =
      `<div class="vacío">Error: ${e.message}</div>`;
  }
}

async function deshacerUltimoCambio() {
  if (!historialUltimoCambio?.valorAnterior) {
    toast("No hay cambio anterior que deshacer", "err");
    return;
  }
  const { entidadId, valorAnterior, accion } = historialUltimoCambio;
  if (
    !confirm(
      `¿Deshacer "${accion}"? Se revertirán los cambios al estado anterior.`,
    )
  )
    return;
  try {
    await api("PUT", `/tareas/${entidadId}`, valorAnterior);
    toast("Cambio revertido");
    historialUltimoCambio = null;
    document.getElementById("undoZona").style.display = "none";
    cargarHistorialTarea();
  } catch (e) {
    toast(e.message, "err");
  }
}

async function buscarTareas() {
  if (!proyActualId) {
    toast("Primero selecciona un proyecto", "err");
    return;
  }
  const params = new URLSearchParams();
  const texto = document.getElementById("fTexto").value.trim();
  const prioridad = document.getElementById("fPrioridad").value;
  const tipo = document.getElementById("fTipo").value;
  if (texto) params.append("texto", texto);
  if (prioridad) params.append("prioridad", prioridad);
  if (tipo) params.append("tipo", tipo);
  const tb = document.getElementById("tbBusqueda");
  tb.innerHTML =
    '<tr><td colspan="5" class="vacío"><span class="spinner"></span></td></tr>';
  try {
    const ts = await api("GET", `/proyectos/${proyActualId}/tareas?${params}`);
    if (!ts.length) {
      tb.innerHTML =
        '<tr><td colspan="5" class="vacío">Sin resultados</td></tr>';
      return;
    }
    tb.innerHTML = ts
      .map(
        (t) => `<tr>
      <td style="color:var(--txt);font-weight:500">${t.titulo}</td>
      <td>${badgeTipo(t.tipo)}</td>
      <td>${badgePrio(t.prioridad)}</td>
      <td class="txt3">${colsActuales.find((c) => c.id === t.columnaId)?.nombre || t.columnaId.slice(-6)}</td>
      <td>${t.estaVencida ? '<span class="badge br">Vencida</span>' : '<span class="badge bg">Activa</span>'}</td>
    </tr>`,
      )
      .join("");
  } catch (e) {
    tb.innerHTML = `<tr><td colspan="5" class="vacío">Error: ${e.message}</td></tr>`;
  }
}

function limpiarFiltros() {
  ["fTexto", "fPrioridad", "fTipo"].forEach(
    (id) => (document.getElementById(id).value = ""),
  );
  document.getElementById("tbBusqueda").innerHTML =
    '<tr><td colspan="5" class="vacío">Aplica un filtro para buscar</td></tr>';
}

async function cargarTareasCompletadas() {
  if (!proyActualId) {
    document.getElementById("listaCompletadas").innerHTML =
      '<div class="vacío">Selecciona un proyecto primero</div>';
    return;
  }
  document.getElementById("listaCompletadas").innerHTML =
    '<span class="spinner"></span>';
  try {
    const tableros = await api("GET", `/proyectos/${proyActualId}/tableros`);
    const columnas = tableros[0]?.columnas || [];
    const colCompletado = columnas.find((c) =>
      c.nombre.toLowerCase().includes("complet"),
    );
    if (!colCompletado) {
      document.getElementById("listaCompletadas").innerHTML =
        '<div class="vacío">No se encontró columna de completadas</div>';
      return;
    }
    const tareas = await api("GET", `/columnas/${colCompletado.id}/tareas`);
    const mias = tareas.filter((t) => t.responsables.includes(S.usuario.id));
    if (!mias.length) {
      document.getElementById("listaCompletadas").innerHTML =
        '<div class="vacío">No tienes tareas completadas asignadas</div>';
      return;
    }
    document.getElementById("listaCompletadas").innerHTML = mias
      .map(
        (t) => `
      <div style="display:flex;align-items:center;justify-content:space-between;
        padding:12px 0;border-bottom:1px solid rgba(63,63,70,.35)">
        <div>
          <div style="font-size:13px;font-weight:500;color:var(--verde)">✓ ${t.titulo}</div>
          <div class="txt3">${badgeTipo(t.tipo)} · ${t.horasRegistradas}h · ${fFecha(t.creadoEn)}</div>
        </div>
        ${badgePrio(t.prioridad)}
      </div>`,
      )
      .join("");
  } catch (e) {
    document.getElementById("listaCompletadas").innerHTML =
      `<div class="vacío">Error: ${e.message}</div>`;
  }
}

/* ══════════ NOTIFICACIONES ══════════ */
async function cargarNotificaciones() {
  if (!S) return;
  const esAdmin = S.usuario.rol === "ADMIN";
  const panelAdmin = document.getElementById("panelAdminNotif");
  const panelMio = document.getElementById("panelMisNotif");
  const btnMarcar = document.getElementById("btnMarcarLeidas");

  // Admin solo ve la tabla global; el resto ve sus propias notificaciones
  if (panelAdmin) panelAdmin.style.display = esAdmin ? "" : "none";
  if (panelMio) panelMio.style.display = esAdmin ? "none" : "";
  if (btnMarcar) btnMarcar.style.display = esAdmin ? "none" : "";

  if (!esAdmin) {
    // Vista normal: mis notificaciones + preferencias
    try {
      const ns = await api("GET", "/notificaciones/");
      const noLeidas = ns.filter((n) => !n.leida).length;
      actualizarBadgeNotif(noLeidas);
      const iconoNotif = (tipo) =>
        ({
          TAREA_ASIGNADA: "📋",
          COMENTARIO_EN_TAREA: "💬",
          MENCION_EN_COMENTARIO: "@",
          ESTADO_TAREA_CAMBIADO: "→",
          TAREA_VENCIDA: "⚠",
          MIEMBRO_INVITADO: "👥",
        })[tipo] || "🔔";

      document.getElementById("listaNotifc").innerHTML = ns.length
        ? ns
            .map((n) => {
              const tieneLink = n.tareaId && n.tituloTarea;
              const accion = tieneLink
                ? `<div style="display:flex;gap:6px;margin-left:auto;align-items:center">
                   <button class="btn btn-outline btn-xs"
                     onclick="irATarea('${n.tareaId}','${(n.tituloTarea || "").replace(/'/g, "\\'")}')"
                     title="Abrir tarea">Ver tarea</button>
                   ${!n.leida ? `<button class="btn btn-ghost btn-xs" onclick="marcarLeida('${n.id}')">✓</button>` : ""}
                 </div>`
                : !n.leida
                  ? `<button class="btn btn-ghost btn-xs" style="margin-left:auto" onclick="marcarLeida('${n.id}')">Leída</button>`
                  : "";
              return `
            <div class="notif-item ${n.leida ? "" : "notif-unread"}">
              <div class="notif-ico" style="${n.leida ? "opacity:.45" : ""}">${iconoNotif(n.tipo)}</div>
              <div style="flex:1;min-width:0">
                <div class="notif-txt" style="${n.leida ? "opacity:.55" : ""}">${n.mensaje}</div>
                ${n.tituloTarea ? `<div class="txt3" style="margin-top:2px">📌 ${n.tituloTarea}</div>` : ""}
                <div class="notif-ts">${fFecha(n.creadoEn)}</div>
              </div>
              ${accion}
            </div>`;
            })
            .join("")
        : '<div class="vacío">Sin notificaciones</div>';

      const prefs = await api("GET", "/notificaciones/preferencias");
      document.getElementById("prefsNotif").innerHTML = `<div>${[
        ["pn1", "notificacionAsignacion", "Asignación de tareas"],
        ["pn2", "notificacionVencimiento", "Alertas de vencimiento"],
        ["pn3", "notificacionComentario", "Comentarios en mis tareas"],
        ["pn4", "notificacionCambioEstado", "Cambios de estado"],
      ]
        .map(
          ([id, campo, label]) => `
        <div class="flex-between" style="padding:12px 0;border-bottom:1px solid rgba(63,63,70,.35)">
          <span class="txt2">${label}</span>
          <div class="toggle ${prefs[campo] ? "on" : ""}" id="${id}" onclick="this.classList.toggle('on')"></div>
        </div>`,
        )
        .join("")}</div>`;
    } catch (e) {
      toast(e.message, "err");
    }
  }
}

/* Navegar desde una notificación directamente al panel de comentarios de la tarea */
async function irATarea(tareaId, tituloTarea) {
  if (!tareaId) return;

  // Marcar notificación como leída si hay alguna sin leer de esta tarea
  // (el backend lo maneja, aquí solo navegamos)

  // Buscar a qué proyecto pertenece la tarea para poder seleccionarla
  try {
    const tarea = await api("GET", `/tareas/${tareaId}`);
    if (tarea.proyectoId) {
      // Sincronizar el proyecto activo
      proyActualId = tarea.proyectoId;
      // Navegar a tareas y cargar el proyecto correcto
      mostrarPantalla("tareas");
      await cargarSelectores();
      const sel = document.getElementById("selTareasProy");
      if (sel) sel.value = tarea.proyectoId;
      await cargarTareasPaginadas(tarea.proyectoId, 1);
      // Pequeña pausa para que el DOM actualice, luego abrir comentarios
      setTimeout(() => {
        abrirPanelComentarios(tareaId, tituloTarea || tarea.titulo);
      }, 300);
    }
  } catch (e) {
    // Si falla la navegación, al menos abrir los comentarios directamente
    toast("Abriendo comentarios...", "ok");
    abrirPanelComentarios(tareaId, tituloTarea);
  }
}

async function marcarLeida(id) {
  try {
    await api("PUT", `/notificaciones/${id}/leer`);
    cargarNotificaciones();
  } catch (e) {
    toast(e.message, "err");
  }
}

async function marcarTodasLeidas() {
  try {
    const r = await api("PUT", "/notificaciones/leer-todas");
    toast(r.mensaje);
    cargarNotificaciones();
  } catch (e) {
    toast(e.message, "err");
  }
}

async function guardarPrefs() {
  const on = (id) => document.getElementById(id)?.classList.contains("on");
  try {
    await api("PUT", "/notificaciones/preferencias", {
      notificacionAsignacion: on("pn1"),
      notificacionVencimiento: on("pn2"),
      notificacionComentario: on("pn3"),
      notificacionCambioEstado: on("pn4"),
    });
    toast("Preferencias guardadas");
  } catch (e) {
    toast(e.message, "err");
  }
}

/* ══════════ PERFIL ══════════ */
async function cargarPerfil() {
  if (!S) return;
  const u = S.usuario;
  // Formulario
  document.getElementById("perNombre").value = u.nombre || "";
  document.getElementById("perDesc").value = u.descripcion || "";
  document.getElementById("perAvatarUrl").value = u.avatarUri || "";
  // Sidebar info
  document.getElementById("perNombreDisplay").textContent = u.nombre || "—";
  document.getElementById("perRolDisplay").textContent = u.rol || "—";
  document.getElementById("perEmailDisplay").textContent = u.email || "—";
  // Seguridad
  const elES = document.getElementById("perEmailSeg");
  if (elES) elES.textContent = u.email || "—";
  const elRS = document.getElementById("perRolSeg");
  if (elRS) elRS.textContent = u.rol || "—";
  aplicarAvatarPerfil(u.avatarUri, u.nombre);
  // Stats: proyectos y último acceso
  try {
    const ps = await api("GET", "/proyectos/");
    const elP = document.getElementById("perStProyectos");
    if (elP) elP.textContent = ps.length;
    // Tareas del usuario
    let totalT = 0;
    await Promise.all(
      ps.map(async (p) => {
        try {
          const res = await api("GET", `/proyectos/${p.id}/tareas?limite=200`);
          const ts = Array.isArray(res) ? res : res.datos || [];
          totalT += ts.filter((t) =>
            (t.responsables || []).includes(u.id),
          ).length;
        } catch (_) {}
      }),
    );
    const elT = document.getElementById("perStTareas");
    if (elT) elT.textContent = totalT;
    const elA = document.getElementById("perStAcceso");
    if (elA)
      elA.textContent = u.ultimoAcceso
        ? new Date(u.ultimoAcceso).toLocaleDateString("es-CO", {
            day: "2-digit",
            month: "short",
          })
        : "—";
  } catch (_) {}
}

function aplicarAvatarPerfil(url, nombre) {
  const img = document.getElementById("perAvatarImg");
  const inicEl = document.getElementById("perAvatarInic");
  if (url) {
    img.src = url;
    img.style.display = "";
    img.onerror = () => {
      img.style.display = "none";
      inicEl.style.display = "";
    };
    inicEl.style.display = "none";
  } else {
    img.style.display = "none";
    inicEl.style.display = "";
    inicEl.textContent = inic(nombre);
  }
}

function previsualizarAvatar(input) {
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    document.getElementById("perAvatarUrl").value = e.target.result;
    aplicarAvatarPerfil(e.target.result, S?.usuario?.nombre || "");
  };
  reader.readAsDataURL(file);
}

function previsualizarAvatarUrl(url) {
  aplicarAvatarPerfil(url || null, S?.usuario?.nombre || "");
}

async function guardarPerfil() {
  document.getElementById("perError").textContent = "";
  const avatarUri =
    document.getElementById("perAvatarUrl").value.trim() || null;
  try {
    const r = await api("PUT", "/usuarios/perfil", {
      nombre: document.getElementById("perNombre").value,
      descripcion: document.getElementById("perDesc").value || null,
      avatarUri,
    });
    S.usuario = { ...S.usuario, ...r };
    localStorage.setItem("tf_s", JSON.stringify(S));
    actualizarUI();
    cargarPerfil();
    toast("Perfil actualizado");
  } catch (e) {
    document.getElementById("perError").textContent = e.message;
  }
}

/* ══════════ NOTIFICACIONES ADMIN — tabla global ══════════ */
async function cargarTodasNotificaciones() {
  const panel = document.getElementById("panelAdminNotif");
  const tb = document.getElementById("tbTodasNotif");
  if (!panel || !tb) return;

  if (S?.usuario?.rol !== "ADMIN") {
    panel.style.display = "none";
    return;
  }
  panel.style.display = "";
  tb.innerHTML =
    '<tr><td colspan="5" class="vacío"><span class="spinner"></span></td></tr>';

  try {
    // Mapa de usuarios para nombres
    const usuarios = await api("GET", "/usuarios/");
    const mapaUsuarios = {};
    usuarios.forEach((u) => {
      mapaUsuarios[u.id] = u;
    });

    // Obtener auditoría de todos los proyectos
    // La ruta ahora puede devolver { datos: [...] } por la paginación
    const proyectos = await api("GET", "/proyectos/");
    const auditoriaRaw = await Promise.all(
      proyectos.map((p) =>
        api("GET", `/proyectos/${p.id}/auditoria?limite=100`)
          .then((res) => {
            // Soportar tanto array plano como respuesta paginada
            return Array.isArray(res) ? res : res.datos || [];
          })
          .catch(() => []),
      ),
    );
    const auditoria = auditoriaRaw
      .flat()
      .filter((r) => r && r.usuarioId) // descartar entradas inválidas
      .sort((a, b) => new Date(b.marca) - new Date(a.marca))
      .slice(0, 80);

    if (!auditoria.length) {
      tb.innerHTML =
        '<tr><td colspan="5" class="vacío">No hay registros de actividad aún</td></tr>';
      return;
    }

    const iconos = {
      CREADA: "✚",
      ACTUALIZADA: "✎",
      MOVIDA: "→",
      ELIMINADA: "✕",
    };
    tb.innerHTML = auditoria
      .map((r) => {
        const u = mapaUsuarios[r.usuarioId];
        const nombreUsuario = u
          ? u.nombre
          : `ID:${(r.usuarioId || "").slice(-6)}`;
        const icono = iconos[r.accion] || "•";
        return `<tr>
        <td style="color:var(--txt);font-weight:500">${icono} ${r.accion || "—"} en ${r.tipoEntidad || "—"}</td>
        <td>${badgeRol(u?.rol || "DEVELOPER")}</td>
        <td>
          <div class="flex" style="gap:6px">
            <div class="avatar avatar-sm">${inic(nombreUsuario)}</div>
            ${nombreUsuario}
          </div>
        </td>
        <td><span class="badge bg">Enviada</span></td>
        <td class="txt3">${fFecha(r.marca)}</td>
      </tr>`;
      })
      .join("");
  } catch (e) {
    tb.innerHTML = `<tr><td colspan="5" class="vacío">Error: ${e.message}</td></tr>`;
  }
}

/* ══════════ REPORTES — tabs por rol ══════════ */
function cambiarTabReporte(nombre, btn) {
  document
    .querySelectorAll("#tabsReporte .htab")
    .forEach((t) => t.classList.remove("activo"));
  document
    .querySelectorAll('[id^="rpanel-"]')
    .forEach((p) => p.classList.remove("activo"));
  btn.classList.add("activo");
  document.getElementById(`rpanel-${nombre}`)?.classList.add("activo");
  const proyId = document.getElementById("selReporteProy")?.value;

  if (nombre === "equipo") {
    if (!proyId) {
      const c = document.getElementById("statsEquipo");
      if (c)
        c.innerHTML =
          '<div class="vacío"><i class="ph ph-folder" style="font-size:28px;opacity:.3;display:block;margin-bottom:8px"></i>Selecciona un proyecto para ver las estadísticas del equipo</div>';
    } else {
      cargarEstadisticasEquipo(proyId);
    }
  }

  if (nombre === "sprint") {
    const c = document.getElementById("contenidoSprint");
    if (!proyId) {
      if (c)
        c.innerHTML =
          '<div class="vacío"><i class="ph ph-lightning" style="font-size:28px;opacity:.3;display:block;margin-bottom:8px"></i>Selecciona un proyecto primero</div>';
    } else {
      if (c)
        c.innerHTML =
          '<div class="vacío">Ingresa el nombre del sprint y haz clic en Generar</div>';
    }
  }

  if (nombre === "metricas" && proyId) cargarReporte(proyId);
  if (nombre === "auditoria_global") cargarAuditoriaGlobal();
}

function inicializarTabsReporte() {
  if (!S) return;
  const rol = S.usuario.rol;
  const esAdmin = rol === "ADMIN";
  const esPMoAdmin = rol === "ADMIN" || rol === "PROJECT_MANAGER";

  // Tabs exclusivos de Admin
  ["tabAuditGlobal", "tabRetencion"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.style.display = esAdmin ? "" : "none";
  });

  // Tabs de sprint y equipo: PM y Admin
  // DEV: se queda solo en el tab de Métricas (visible para todos)
  // Los tabs de sprint y equipo existen en el HTML, solo los ocultamos para DEV
  const tabSprint = document.querySelector("#tabsReporte .htab:nth-child(2)");
  const tabEquipo = document.querySelector("#tabsReporte .htab:nth-child(3)");
  if (tabSprint) tabSprint.style.display = esPMoAdmin ? "" : "none";
  if (tabEquipo) tabEquipo.style.display = esPMoAdmin ? "" : "none";
}

async function generarReporteSprint() {
  const proyId = document.getElementById("selReporteProy")?.value;
  if (!proyId) {
    toast("Selecciona un proyecto primero", "err");
    return;
  }
  const sprint =
    document.getElementById("sprintNombre").value.trim() || "Sprint actual";
  const contenedor = document.getElementById("contenidoSprint");
  contenedor.innerHTML = '<span class="spinner"></span>';
  try {
    const metricas = await api("GET", `/proyectos/${proyId}/metricas`);
    const proyecto = await api("GET", `/proyectos/${proyId}`);
    const pct = Math.round(metricas.progreso || 0);
    const completadas = metricas.tareasCompletadas || 0;
    const total = metricas.totalTareas || 0;
    const vencidas = metricas.tareasVencidas || 0;
    const estadoEntradas = Object.entries(metricas.tareasPorEstado || {});
    const prioEntradas = Object.entries(metricas.tareasPorPrioridad || {});
    const prioColores = {
      BAJA: "var(--green)",
      MEDIA: "var(--amber)",
      ALTA: "var(--red)",
      URGENTE: "var(--purple)",
    };
    const maxCant = Math.max(...estadoEntradas.map(([, v]) => v), 1);

    contenedor.innerHTML = `
      <div class="sprint-reporte">
        <div class="sprint-header">
          <div>
            <div class="sprint-titulo"><i class="ph ph-lightning" style="color:var(--amber)"></i> ${sprint}</div>
            <div class="sprint-sub">${proyecto.nombre} · Generado ${fFecha(new Date().toISOString())}</div>
          </div>
          <div class="sprint-progreso-circ">
            <svg viewBox="0 0 60 60" width="60" height="60">
              <circle cx="30" cy="30" r="24" fill="none" stroke="var(--b1)" stroke-width="5"/>
              <circle cx="30" cy="30" r="24" fill="none" stroke="var(--a)" stroke-width="5"
                stroke-dasharray="${2 * Math.PI * 24}" stroke-dashoffset="${2 * Math.PI * 24 * (1 - pct / 100)}"
                stroke-linecap="round" transform="rotate(-90 30 30)"/>
            </svg>
            <span class="sprint-pct-txt">${pct}%</span>
          </div>
        </div>

        <div class="sprint-kpis">
          <div class="sprint-kpi">
            <i class="ph ph-check-square" style="color:var(--a)"></i>
            <div class="sprint-kpi-v">${total}</div>
            <div class="sprint-kpi-l">Total tareas</div>
          </div>
          <div class="sprint-kpi">
            <i class="ph ph-check-circle" style="color:var(--green)"></i>
            <div class="sprint-kpi-v">${completadas}</div>
            <div class="sprint-kpi-l">Completadas</div>
          </div>
          <div class="sprint-kpi">
            <i class="ph ph-warning-circle" style="color:var(--red)"></i>
            <div class="sprint-kpi-v" style="color:${vencidas > 0 ? "var(--red)" : "var(--green)"}">${vencidas}</div>
            <div class="sprint-kpi-l">Vencidas</div>
          </div>
          <div class="sprint-kpi">
            <i class="ph ph-percent" style="color:var(--amber)"></i>
            <div class="sprint-kpi-v">${pct}%</div>
            <div class="sprint-kpi-l">Progreso</div>
          </div>
        </div>

        <div class="sprint-dos-col">
          <div>
            <div class="sprint-section-t"><i class="ph ph-kanban"></i> Por columna</div>
            ${
              estadoEntradas
                .map(
                  ([col, cant]) => `
              <div class="sprint-bar-row">
                <span class="sprint-bar-label">${col}</span>
                <div class="sprint-bar-track">
                  <div class="sprint-bar-fill" style="width:${Math.round((cant / maxCant) * 100)}%"></div>
                </div>
                <span class="sprint-bar-val">${cant}</span>
              </div>`,
                )
                .join("") || '<div class="vacío">Sin datos</div>'
            }
          </div>
          <div>
            <div class="sprint-section-t"><i class="ph ph-chart-bar-horizontal"></i> Por prioridad</div>
            ${
              prioEntradas
                .map(
                  ([prio, cant]) => `
              <div class="sprint-bar-row">
                <span class="sprint-bar-label">${prio}</span>
                <div class="sprint-bar-track">
                  <div class="sprint-bar-fill" style="width:${Math.round((cant / total) * 100)}%;background:${prioColores[prio] || "var(--a)"}"></div>
                </div>
                <span class="sprint-bar-val">${cant}</span>
              </div>`,
                )
                .join("") || '<div class="vacío">Sin datos</div>'
            }
          </div>
        </div>
      </div>`;
  } catch (e) {
    contenedor.innerHTML = `<div class="vacío">Error: ${e.message}</div>`;
  }
}

async function cargarEstadisticasEquipo(proyId) {
  const contenedor = document.getElementById("statsEquipo");
  if (!proyId) {
    contenedor.innerHTML = '<div class="vacío">Selecciona un proyecto</div>';
    return;
  }
  contenedor.innerHTML = '<span class="spinner"></span>';
  try {
    const [metricas, miembros] = await Promise.all([
      api("GET", `/proyectos/${proyId}/metricas`),
      api("GET", `/proyectos/${proyId}/miembros`),
    ]);
    const tareasPorUser = metricas.tareasPorUsuario || {};
    if (!miembros.length) {
      contenedor.innerHTML = '<div class="vacío">Sin miembros</div>';
      return;
    }
    contenedor.innerHTML = `
      <div class="tabla-wrap">
        <table>
          <thead><tr><th>Miembro</th><th>Rol</th><th>Tareas asignadas</th><th>Carga</th></tr></thead>
          <tbody>${miembros
            .map((m) => {
              const cantidad = tareasPorUser[m.id] || 0;
              const max = Math.max(...Object.values(tareasPorUser), 1);
              const pct = Math.round((cantidad / max) * 100);
              return `<tr>
              <td>
                <div class="flex" style="gap:8px">
                  <div class="avatar avatar-sm">${inic(m.nombre)}</div>${m.nombre}
                </div>
              </td>
              <td>${badgeRol(m.rol)}</td>
              <td><span class="badge bi">${cantidad}</span></td>
              <td style="min-width:120px">
                <div class="prog" style="height:6px">
                  <div class="prog-bar" style="width:${pct}%"></div>
                </div>
              </td>
            </tr>`;
            })
            .join("")}</tbody>
        </table>
      </div>`;
  } catch (e) {
    contenedor.innerHTML = `<div class="vacío">Error: ${e.message}</div>`;
  }
}

/* exportarReporte eliminado */

async function cargarAuditoriaGlobal() {
  const contenedor = document.getElementById("listaAuditoriaGlobal");
  if (!contenedor) return;
  contenedor.innerHTML = '<span class="spinner"></span>';
  try {
    const proyectos = await api("GET", "/proyectos/");
    const mapaUAudit = await _obtenerMapaUsuarios();

    const auditoriaRaw = await Promise.all(
      proyectos.map((p) =>
        api("GET", `/proyectos/${p.id}/auditoria?limite=100`)
          .then((res) => (Array.isArray(res) ? res : res.datos || []))
          .catch(() => []),
      ),
    );
    const todaAuditoria = auditoriaRaw
      .flat()
      .filter((r) => r && r.usuarioId)
      .sort((a, b) => new Date(b.marca) - new Date(a.marca));

    if (!todaAuditoria.length) {
      contenedor.innerHTML =
        '<div class="vacío">Sin registros de auditoría global</div>';
      return;
    }
    contenedor.innerHTML = `<div class="timeline">${todaAuditoria
      .slice(0, 80)
      .map((r, i) => {
        const uAudit = mapaUAudit[r.usuarioId];
        const nombreAudit = uAudit
          ? uAudit.nombre
          : `ID:${(r.usuarioId || "").slice(-6)}`;
        const avAudit = uAudit
          ? `<div class="avatar avatar-sm" style="display:inline-flex;vertical-align:middle;margin-right:4px">${inic(uAudit.nombre)}</div>`
          : "";
        return `
        <div class="tl-item ${i === 0 ? "reciente" : ""}">
          <div class="tl-accion"><strong>${r.accion || "—"}</strong> en ${r.tipoEntidad || "—"}</div>
          <div class="tl-meta">${avAudit}${nombreAudit} · ${fFecha(r.marca)}</div>
        </div>`;
      })
      .join("")}</div>`;
  } catch (e) {
    contenedor.innerHTML = `<div class="vacío">Error: ${e.message}</div>`;
  }
}

/* guardarPoliticaRetencion eliminado */

/* ══════════ POLÍTICA DE RETENCIÓN ══════════ */
function aplicarPoliticaRetencion() {
  const dias = document.getElementById("diasRetencion")?.value;
  const nivel = document.getElementById("nivelRetencion")?.value;
  const msg = document.getElementById("retencionMensaje");
  if (!dias || parseInt(dias) < 7) {
    if (msg) msg.textContent = "✕ El mínimo es 7 días";
    return;
  }
  localStorage.setItem("tf_retencion", JSON.stringify({ dias, nivel }));
  if (msg)
    msg.textContent = `✓ Política aplicada: conservar ${dias} días (nivel: ${nivel})`;
  toast("Política de retención guardada");
}

/* ═══════════════════════════════════════════════════
   REGISTRO DE USUARIO
════════════════════════════════════════════════════ */
function seleccionarRol(el) {
  document
    .querySelectorAll(".registro-rol-opt")
    .forEach((o) => o.classList.remove("activo"));
  el.classList.add("activo");
  const hidden = document.getElementById("rRol");
  if (hidden) hidden.value = el.dataset.val;
}

function toggleVerPassReg() {
  const campo = document.getElementById("rPass");
  const icono = document.getElementById("iconoVerPassReg");
  if (!campo) return;
  if (campo.type === "password") {
    campo.type = "text";
    if (icono) icono.className = "ph ph-eye-slash";
  } else {
    campo.type = "password";
    if (icono) icono.className = "ph ph-eye";
  }
}

async function crearUsuario() {
  const errEl = document.getElementById("rError");
  if (errEl) errEl.textContent = "";
  const nombre = document.getElementById("rNombre")?.value?.trim();
  const email = document.getElementById("rEmail")?.value?.trim();
  const pass = document.getElementById("rPass")?.value?.trim();
  const rol = document.getElementById("rRol")?.value || "DEVELOPER";
  if (!nombre || !email || !pass) {
    if (errEl) errEl.textContent = "Todos los campos son obligatorios";
    return;
  }
  const btn = document.querySelector("#pantalla-registro .btn-primary");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Creando...';
  }
  try {
    await api("POST", "/usuarios/registro", {
      nombre,
      email,
      contrasena: pass,
      rol,
    });
    // Limpiar formulario
    ["rNombre", "rEmail", "rPass"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.value = "";
    });
    // Resetear selector de rol a Developer
    document
      .querySelectorAll(".registro-rol-opt")
      .forEach((o) => o.classList.remove("activo"));
    const dev = document.querySelector(
      '.registro-rol-opt[data-val="DEVELOPER"]',
    );
    if (dev) dev.classList.add("activo");
    const hidden = document.getElementById("rRol");
    if (hidden) hidden.value = "DEVELOPER";
    _invalidarCacheUsuarios();
    toast("Usuario creado correctamente");
  } catch (e) {
    if (errEl) errEl.textContent = e.message;
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="ph ph-user-plus"></i> Crear usuario';
    }
  }
}
