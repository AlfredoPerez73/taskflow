/* ═══════════════════════════════════════════════════
   TaskFlow — subtareas.js
   Panel de subtareas (Patrón Builder) +
   Panel de envío de notificaciones externas (Adapter + Factory Method)
════════════════════════════════════════════════════ */

/* ══════════════════════════════════════════════════
   SUBTAREAS — Panel lateral tipo drawer
══════════════════════════════════════════════════ */

let _subtareasTareaId = null;
let _subtareasTitulo = "";

/**
 * Abre el panel de subtareas para una tarea.
 * Se puede llamar desde la tarjeta Kanban o desde la tabla de tareas.
 */
async function abrirPanelSubtareas(tareaId, tituloTarea) {
  _subtareasTareaId = tareaId;
  _subtareasTitulo = tituloTarea;

  // Crear el panel si no existe
  let panel = document.getElementById("panelSubtareas");
  if (!panel) {
    panel = document.createElement("div");
    panel.id = "panelSubtareas";
    panel.innerHTML = _htmlPanelSubtareas();
    document.body.appendChild(panel);

    // Cerrar al hacer clic en el backdrop
    panel
      .querySelector(".subtarea-backdrop")
      .addEventListener("click", cerrarPanelSubtareas);
  }

  panel.querySelector("#stTareaTitle").textContent = tituloTarea;
  panel.classList.add("open");
  document.body.style.overflow = "hidden";

  await _cargarSubtareas(tareaId);
}

function cerrarPanelSubtareas() {
  const panel = document.getElementById("panelSubtareas");
  if (panel) panel.classList.remove("open");
  document.body.style.overflow = "";
}

function _htmlPanelSubtareas() {
  return `
<div class="subtarea-backdrop"></div>
<div class="subtarea-drawer">
  <div class="subtarea-header">
    <div>
      <div class="subtarea-label"><i class="ph ph-tree-structure"></i> Subtareas · Builder</div>
      <div class="subtarea-title" id="stTareaTitle">—</div>
    </div>
    <button class="btn btn-ghost btn-xs" onclick="cerrarPanelSubtareas()" style="font-size:18px">✕</button>
  </div>

  <div class="subtarea-progress-wrap" id="stProgressWrap" style="display:none">
    <div class="subtarea-progress-label">
      <span id="stProgLabel">0 / 0</span>
      <span id="stProgPct" style="font-family:var(--mono);font-size:11px;color:var(--green)">0%</span>
    </div>
    <div class="prog"><div class="prog-bar" id="stProgBar" style="width:0%;background:var(--green)"></div></div>
  </div>

  <div class="subtarea-lista" id="stLista">
    <div class="vacío"><span class="spinner"></span></div>
  </div>

  <div class="subtarea-form">
    <div class="subtarea-form-title"><i class="ph ph-plus-circle" style="color:var(--a)"></i> Nueva subtarea — Builder</div>
    <div class="fg" style="margin-bottom:8px">
      <input class="finput" id="stNuevoTitulo" placeholder="Título de la subtarea..."
        onkeydown="if(event.key==='Enter')crearSubtarea()">
    </div>
    <div class="fg" style="margin-bottom:8px">
      <textarea class="ftextarea" id="stNuevoDesc" placeholder="Descripción (opcional)..." style="min-height:54px;resize:none"></textarea>
    </div>
    <div class="frow" style="margin-bottom:8px">
      <div class="fg">
        <label class="flabel">Fecha vencimiento</label>
        <input class="finput" id="stNuevoFV" type="datetime-local">
      </div>
      <div class="fg">
        <label class="flabel">Responsables</label>
        <div id="stRespLista" class="resp-lista" style="max-height:72px;overflow-y:auto"></div>
      </div>
    </div>
    <div class="ferror" id="stError"></div>
    <div style="display:flex;gap:8px;justify-content:flex-end">
      <button class="btn btn-ghost btn-sm" onclick="document.getElementById('stNuevoTitulo').value=''">Limpiar</button>
      <button class="btn btn-primary btn-sm" id="stBtnCrear" onclick="crearSubtarea()">
        <i class="ph ph-plus"></i> Crear subtarea
      </button>
    </div>
  </div>
</div>`;
}

async function _cargarSubtareas(tareaId) {
  const lista = document.getElementById("stLista");
  if (!lista) return;
  lista.innerHTML = '<div class="vacío"><span class="spinner"></span></div>';

  // Cargar responsables para el selector
  _poblarRespSubtarea();

  try {
    const subtareas = await api("GET", `/tareas/${tareaId}/subtareas`);
    _renderizarSubtareas(subtareas);
  } catch (e) {
    lista.innerHTML = `<div class="vacío">Error: ${e.message}</div>`;
  }
}

function _renderizarSubtareas(subtareas) {
  const lista = document.getElementById("stLista");
  const wrap = document.getElementById("stProgressWrap");
  if (!lista) return;

  if (!subtareas.length) {
    lista.innerHTML = `
      <div class="vacío" style="padding:32px 16px">
        <i class="ph ph-tree-structure" style="font-size:36px;display:block;margin-bottom:10px;opacity:.2"></i>
        Sin subtareas. Usa el Builder para crear la primera.
      </div>`;
    if (wrap) wrap.style.display = "none";
    return;
  }

  // Barra de progreso
  const total = subtareas.length;
  const completadas = subtareas.filter((s) => s.completada).length;
  const pct = Math.round((completadas / total) * 100);
  if (wrap) {
    wrap.style.display = "";
    document.getElementById("stProgLabel").textContent =
      `${completadas} / ${total} completadas`;
    document.getElementById("stProgPct").textContent = `${pct}%`;
    document.getElementById("stProgBar").style.width = `${pct}%`;
  }

  lista.innerHTML = subtareas
    .map(
      (s) => `
    <div class="subtarea-item ${s.completada ? "completada" : ""}" id="st-${s.id}">
      <div class="subtarea-check" onclick="_toggleSubtarea('${s.id}')"
        title="${s.completada ? "Desmarcar" : "Completar"}">
        ${
          s.completada
            ? '<i class="ph ph-check-circle" style="color:var(--green);font-size:18px"></i>'
            : '<i class="ph ph-circle" style="color:var(--t3);font-size:18px"></i>'
        }
      </div>
      <div class="subtarea-body">
        <div class="subtarea-item-titulo">${s.titulo}</div>
        ${s.descripcion ? `<div class="subtarea-item-desc">${s.descripcion}</div>` : ""}
        <div class="subtarea-item-meta">
          ${s.fechaVencimiento ? `<span class="txt3"><i class="ph ph-calendar-blank"></i> ${fFecha(s.fechaVencimiento)}</span>` : ""}
          ${s.responsables?.length ? `<span class="txt3"><i class="ph ph-user"></i> ${s.responsables.length}</span>` : ""}
        </div>
      </div>
      <div class="subtarea-acciones">
        <button class="btn btn-red btn-xs" onclick="_eliminarSubtarea('${s.id}')" title="Eliminar">
          <i class="ph ph-trash"></i>
        </button>
      </div>
    </div>`,
    )
    .join("");
}

async function crearSubtarea() {
  const titulo = document.getElementById("stNuevoTitulo")?.value?.trim();
  const errEl = document.getElementById("stError");
  if (errEl) errEl.textContent = "";

  if (!titulo) {
    if (errEl) errEl.textContent = "El título es obligatorio";
    return;
  }
  if (!_subtareasTareaId) return;

  const btn = document.getElementById("stBtnCrear");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>';
  }

  const resp = getSeleccionados("stRespLista");
  const fv = document.getElementById("stNuevoFV")?.value || null;
  const desc = document.getElementById("stNuevoDesc")?.value?.trim() || null;

  try {
    await api("POST", `/tareas/${_subtareasTareaId}/subtareas`, {
      titulo,
      descripcion: desc,
      responsables: resp,
      fechaVencimiento: fv || null,
    });
    // Limpiar form
    document.getElementById("stNuevoTitulo").value = "";
    document.getElementById("stNuevoDesc").value = "";
    document.getElementById("stNuevoFV").value = "";
    document
      .querySelectorAll("#stRespLista .resp-chip")
      .forEach((c) => c.classList.remove("sel"));

    toast("Subtarea creada — Builder ✓");
    await _cargarSubtareas(_subtareasTareaId);
  } catch (e) {
    if (errEl) errEl.textContent = e.message;
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="ph ph-plus"></i> Crear subtarea';
    }
  }
}

async function _toggleSubtarea(subtareaId) {
  try {
    await api("POST", `/subtareas/${subtareaId}/toggle`);
    await _cargarSubtareas(_subtareasTareaId);
  } catch (e) {
    toast(e.message, "err");
  }
}

async function _eliminarSubtarea(subtareaId) {
  if (!confirm("¿Eliminar esta subtarea?")) return;
  try {
    await api("DELETE", `/subtareas/${subtareaId}`);
    toast("Subtarea eliminada");
    await _cargarSubtareas(_subtareasTareaId);
  } catch (e) {
    toast(e.message, "err");
  }
}

function _poblarRespSubtarea() {
  const c = document.getElementById("stRespLista");
  if (!c) return;
  if (!miembrosActuales?.length) {
    c.innerHTML =
      '<span class="txt3" style="font-size:11px">Sin developers</span>';
    return;
  }
  c.innerHTML = miembrosActuales
    .map(
      (m) => `
    <div class="resp-chip" onclick="toggleResp(this)" data-id="${m.id}"
      style="font-size:10px;padding:2px 7px 2px 4px">
      <div class="avatar avatar-sm" style="width:16px;height:16px;font-size:8px">${inic(m.nombre)}</div>
      ${m.nombre.split(" ")[0]}
    </div>`,
    )
    .join("");
}

/* ══════════════════════════════════════════════════
   NOTIFICACIONES EXTERNAS — Modal Adapter + Factory
══════════════════════════════════════════════════ */

let _notifDestinatarios = []; // cache de usuarios cargados

async function abrirModalNotifExterna() {
  let modal = document.getElementById("mNotifExterna");
  if (!modal) {
    modal = document.createElement("div");
    modal.className = "overlay";
    modal.id = "mNotifExterna";
    modal.innerHTML = _htmlModalNotifExterna();
    document.body.appendChild(modal);
    modal.addEventListener("click", (e) => {
      if (e.target === modal) cerrarModal("mNotifExterna");
    });
  }
  abrirModal("mNotifExterna");
  await _cargarDestinatariosNotif();
}

function _htmlModalNotifExterna() {
  return `
<div class="modal" style="width:520px">
  <div class="flex-between" style="margin-bottom:6px">
    <div class="modal-t" style="margin-bottom:0">
      <i class="ph ph-paper-plane-right" style="color:var(--a)"></i>
      Enviar notificación externa — Adapter
    </div>
    <button class="btn btn-ghost btn-xs" onclick="cerrarModal('mNotifExterna')">✕</button>
  </div>
  <div style="background:var(--s2);border:1px solid var(--b1);border-radius:var(--r);padding:10px 12px;margin-bottom:16px">
    <div style="font-size:11px;color:var(--t3);font-family:var(--mono);line-height:1.6">
      <strong style="color:var(--a2)">Factory Method + Adapter:</strong>
      ProveedorNotificacion → Fábrica concreta → Adaptador → API externa
    </div>
    <div class="notif-canal-flow" id="notifCanalFlow">
      <span class="notif-flow-step">ProveedorNotificacion</span>
      <span class="notif-flow-arrow">→</span>
      <span class="notif-flow-step active" id="flowFabrica">FabricaEmail</span>
      <span class="notif-flow-arrow">→</span>
      <span class="notif-flow-step active" id="flowAdapter">EmailAdaptee</span>
      <span class="notif-flow-arrow">→</span>
      <span class="notif-flow-step active" id="flowApi">EmailAPI</span>
    </div>
  </div>

  <div class="fg">
    <label class="flabel">Canal de envío</label>
    <div class="notif-canal-btns" id="notifCanalBtns">
      <button class="notif-canal-btn activo" data-canal="email" onclick="_selCanal(this)">
        <i class="ph ph-envelope"></i> Email
      </button>
      <button class="notif-canal-btn" data-canal="whatsapp" onclick="_selCanal(this)">
        <i class="ph ph-whatsapp-logo"></i> WhatsApp
      </button>
      <button class="notif-canal-btn" data-canal="sms" onclick="_selCanal(this)">
        <i class="ph ph-chat-text"></i> SMS
      </button>
    </div>
    <input type="hidden" id="notifCanal" value="email">
  </div>

  <div class="fg">
    <label class="flabel">Destinatario</label>
    <select class="fselect" id="notifDestinatario">
      <option value="">— Cargando usuarios... —</option>
    </select>
    <div id="notifContactoInfo" style="margin-top:5px;font-size:11px;color:var(--t3);font-family:var(--mono)"></div>
  </div>

  <div class="fg">
    <label class="flabel">Asunto (email)</label>
    <input class="finput" id="notifAsunto" value="Notificación TaskFlow" placeholder="Asunto del email">
  </div>

  <div class="fg">
    <label class="flabel">Mensaje</label>
    <textarea class="ftextarea" id="notifMensaje"
      placeholder="Escribe el mensaje de la notificación..."
      style="min-height:80px"></textarea>
  </div>

  <div id="notifResultado" style="display:none;margin-bottom:12px"></div>
  <div class="ferror" id="notifError"></div>

  <div class="modal-actions">
    <button class="btn btn-ghost" onclick="cerrarModal('mNotifExterna')">Cancelar</button>
    <button class="btn btn-outline btn-sm" onclick="_probarTodosCanales()" id="btnProbar">
      <i class="ph ph-broadcast"></i> Probar todos
    </button>
    <button class="btn btn-primary" onclick="_enviarNotifExterna()" id="btnEnviarNotif">
      <i class="ph ph-paper-plane-right"></i> Enviar
    </button>
  </div>
</div>`;
}

const _FLOW_MAP = {
  email: { fabrica: "FabricaEmail", adapter: "EmailAdaptee", api: "EmailAPI" },
  whatsapp: {
    fabrica: "FabricaWhatsApp",
    adapter: "WhatsAppAdaptee",
    api: "WhatsAppAPI",
  },
  sms: { fabrica: "FabricaSms", adapter: "SmsAdaptee", api: "SmsAPI" },
};

function _selCanal(btn) {
  document
    .querySelectorAll(".notif-canal-btn")
    .forEach((b) => b.classList.remove("activo"));
  btn.classList.add("activo");
  const canal = btn.dataset.canal;
  document.getElementById("notifCanal").value = canal;

  // Actualizar diagrama de flujo
  const flow = _FLOW_MAP[canal];
  if (flow) {
    document.getElementById("flowFabrica").textContent = flow.fabrica;
    document.getElementById("flowAdapter").textContent = flow.adapter;
    document.getElementById("flowApi").textContent = flow.api;
  }

  // Actualizar info de contacto
  _actualizarContactoInfo();
}

async function _cargarDestinatariosNotif() {
  try {
    const us = await api("GET", "/usuarios/activos");
    _notifDestinatarios = us;
    const sel = document.getElementById("notifDestinatario");
    if (!sel) return;
    sel.innerHTML =
      '<option value="">— Selecciona un destinatario —</option>' +
      us
        .map((u) => `<option value="${u.id}">${u.nombre} (${u.rol})</option>`)
        .join("");
    sel.addEventListener("change", _actualizarContactoInfo);
  } catch (_) {}
}

function _actualizarContactoInfo() {
  const sel = document.getElementById("notifDestinatario");
  const info = document.getElementById("notifContactoInfo");
  const canal = document.getElementById("notifCanal")?.value || "email";
  if (!sel || !info) return;

  const usuario = _notifDestinatarios.find((u) => u.id === sel.value);
  if (!usuario) {
    info.textContent = "";
    return;
  }

  const contactoMap = {
    email: `📧 ${usuario.email}`,
    whatsapp: `📱 ${usuario.telefono || "Sin teléfono registrado (configura en Notificaciones → Contacto)"}`,
    sms: `💬 ${usuario.telefono || "Sin teléfono registrado"}`,
  };
  info.innerHTML = `<span style="color:var(--a2)">Contacto:</span> ${contactoMap[canal] || usuario.email}`;
}

async function _enviarNotifExterna() {
  const canal = document.getElementById("notifCanal")?.value;
  const userId = document.getElementById("notifDestinatario")?.value;
  const asunto = document.getElementById("notifAsunto")?.value?.trim();
  const mensaje = document.getElementById("notifMensaje")?.value?.trim();
  const errEl = document.getElementById("notifError");
  const resEl = document.getElementById("notifResultado");
  if (errEl) errEl.textContent = "";
  if (resEl) resEl.style.display = "none";

  if (!userId) {
    if (errEl) errEl.textContent = "Selecciona un destinatario";
    return;
  }
  if (!mensaje) {
    if (errEl) errEl.textContent = "El mensaje es obligatorio";
    return;
  }

  const btn = document.getElementById("btnEnviarNotif");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Enviando...';
  }

  try {
    const r = await api("POST", "/notificaciones/enviar-externo", {
      canal,
      usuarioId: userId,
      mensaje,
      asunto,
    });
    _mostrarResultadoNotif([{ canal, ...r }]);
    toast(`Notificación enviada por ${canal} ✓`);
  } catch (e) {
    if (errEl) errEl.textContent = e.message;
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="ph ph-paper-plane-right"></i> Enviar';
    }
  }
}

async function _probarTodosCanales() {
  const userId = document.getElementById("notifDestinatario")?.value;
  const errEl = document.getElementById("notifError");
  if (!userId) {
    if (errEl) errEl.textContent = "Selecciona un destinatario";
    return;
  }

  const btn = document.getElementById("btnProbar");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Probando...';
  }
  if (errEl) errEl.textContent = "";

  try {
    const r = await api("POST", "/notificaciones/probar-canales", {
      usuarioId: userId,
    });
    const resultados = Object.entries(r.resultados || {}).map(
      ([canal, res]) => ({ canal, ...res }),
    );
    _mostrarResultadoNotif(resultados);
    toast("Prueba de canales completada");
  } catch (e) {
    if (errEl) errEl.textContent = e.message;
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="ph ph-broadcast"></i> Probar todos';
    }
  }
}

function _mostrarResultadoNotif(resultados) {
  const resEl = document.getElementById("notifResultado");
  if (!resEl) return;
  resEl.style.display = "";
  resEl.innerHTML = `
    <div style="background:var(--s2);border:1px solid var(--b1);border-radius:var(--r);padding:10px 12px">
      <div style="font-size:11px;font-weight:600;color:var(--t2);margin-bottom:8px;font-family:var(--mono)">
        RESULTADO DEL ADAPTER
      </div>
      ${resultados
        .map(
          (r) => `
        <div style="display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid var(--b0)">
          <span style="width:20px;text-align:center">
            ${r.enviada ? "✅" : "❌"}
          </span>
          <span class="badge ${r.enviada ? "bg" : "br"}">${(r.canal || "?").toUpperCase()}</span>
          <span style="font-size:11px;color:var(--t3);font-family:var(--mono);flex:1">${r.detalle || ""}</span>
          ${r.contacto_usado ? `<span style="font-size:10px;color:var(--t3)">${r.contacto_usado}</span>` : ""}
        </div>`,
        )
        .join("")}
    </div>`;
}

/* ══════════════════════════════════════════════════
   SSE — Stream de notificaciones en tiempo real
══════════════════════════════════════════════════ */

let _sseConexion = null;

function conectarStream() {
  if (!S?.token_acceso) return;
  if (_sseConexion) _sseConexion.close();

  _sseConexion = new EventSource(
    `${API}/notificaciones/stream?token=${S.token_acceso}`,
  );

  _sseConexion.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.tipo === "ping" || data.tipo === "conectado") return;
      if (data.tipo === "notificacion") {
        // Incrementar badge
        const badge = document.getElementById("badgeNotif");
        if (badge) {
          const n = parseInt(badge.textContent || "0") + 1;
          badge.textContent = n;
          badge.style.display = "";
        }
        // Toast flotante
        toast(`🔔 ${data.mensaje || "Nueva notificación"}`);
      }
    } catch (_) {}
  };

  _sseConexion.onerror = () => {
    // Reconectar automáticamente después de 5 segundos
    setTimeout(() => {
      if (S?.token_acceso) conectarStream();
    }, 5000);
  };
}

function desconectarStream() {
  if (_sseConexion) {
    _sseConexion.close();
    _sseConexion = null;
  }
}

// Nota: el SSE se inicia al hacer login en app.js
// Aquí exponemos la función para que app.js la llame
window._conectarStreamSSE = conectarStream;
window._desconectarStreamSSE = desconectarStream;

/* ══════════════════════════════════════════════════
   ESTILOS INLINE para los nuevos componentes
══════════════════════════════════════════════════ */

(function _inyectarEstilos() {
  const css = `
/* ── Panel Subtareas ── */
#panelSubtareas {
  position: fixed;
  inset: 0;
  z-index: 300;
  pointer-events: none;
}
#panelSubtareas.open {
  pointer-events: auto;
}
.subtarea-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,.55);
  opacity: 0;
  transition: opacity .2s;
}
#panelSubtareas.open .subtarea-backdrop {
  opacity: 1;
}
.subtarea-drawer {
  position: absolute;
  top: 0;
  right: 0;
  width: 460px;
  max-width: 96vw;
  height: 100%;
  background: var(--s1);
  border-left: 1px solid var(--b2);
  display: flex;
  flex-direction: column;
  transform: translateX(100%);
  transition: transform .22s cubic-bezier(.4,0,.2,1);
  box-shadow: -12px 0 48px rgba(0,0,0,.4);
}
#panelSubtareas.open .subtarea-drawer {
  transform: translateX(0);
}
.subtarea-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 18px 20px 12px;
  border-bottom: 1px solid var(--b1);
  flex-shrink: 0;
}
.subtarea-label {
  font-size: 10px;
  font-weight: 500;
  color: var(--a2);
  letter-spacing: .08em;
  text-transform: uppercase;
  font-family: var(--mono);
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 5px;
}
.subtarea-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--t1);
  letter-spacing: -.02em;
  line-height: 1.3;
}
.subtarea-progress-wrap {
  padding: 12px 20px 8px;
  border-bottom: 1px solid var(--b0);
  flex-shrink: 0;
}
.subtarea-progress-label {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--t3);
  margin-bottom: 5px;
}
.subtarea-lista {
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px;
}
.subtarea-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px;
  border-radius: var(--r);
  margin-bottom: 4px;
  border: 1px solid var(--b0);
  transition: background .1s, border-color .1s;
}
.subtarea-item:hover {
  background: var(--s2);
  border-color: var(--b1);
}
.subtarea-item.completada {
  opacity: .55;
}
.subtarea-item.completada .subtarea-item-titulo {
  text-decoration: line-through;
  color: var(--t3);
}
.subtarea-check {
  cursor: pointer;
  flex-shrink: 0;
  margin-top: 1px;
  transition: transform .1s;
}
.subtarea-check:hover {
  transform: scale(1.15);
}
.subtarea-body {
  flex: 1;
  min-width: 0;
}
.subtarea-item-titulo {
  font-size: 13px;
  font-weight: 500;
  color: var(--t1);
  margin-bottom: 2px;
}
.subtarea-item-desc {
  font-size: 12px;
  color: var(--t3);
  margin-bottom: 4px;
}
.subtarea-item-meta {
  display: flex;
  gap: 8px;
  font-size: 10px;
  color: var(--t3);
  font-family: var(--mono);
}
.subtarea-acciones {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity .15s;
}
.subtarea-item:hover .subtarea-acciones {
  opacity: 1;
}
.subtarea-form {
  border-top: 1px solid var(--b1);
  padding: 14px 16px;
  background: var(--s2);
  flex-shrink: 0;
}
.subtarea-form-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--t2);
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* ── Notificaciones externas ── */
.notif-canal-flow {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  flex-wrap: wrap;
}
.notif-flow-step {
  font-family: var(--mono);
  font-size: 10px;
  padding: 3px 8px;
  border-radius: 4px;
  background: var(--s3);
  color: var(--t3);
  border: 1px solid var(--b1);
  transition: all .2s;
}
.notif-flow-step.active {
  background: var(--abg);
  color: var(--a2);
  border-color: rgba(108,99,255,.3);
}
.notif-flow-arrow {
  color: var(--t3);
  font-size: 12px;
}
.notif-canal-btns {
  display: flex;
  gap: 8px;
  margin-top: 6px;
}
.notif-canal-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  border-radius: var(--r);
  border: 1.5px solid var(--b1);
  background: var(--s2);
  color: var(--t2);
  font-size: 12px;
  font-family: var(--sans);
  cursor: pointer;
  transition: var(--t);
}
.notif-canal-btn:hover {
  border-color: var(--b2);
  color: var(--t1);
}
.notif-canal-btn.activo {
  border-color: var(--a);
  background: var(--abg);
  color: var(--a2);
}
.notif-canal-btn i {
  font-size: 16px;
}
`;
  const style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);
})();
