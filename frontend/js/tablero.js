/* ═══════════════════════════════════════════════════
   TaskFlow — tablero.js
   Kanban: carga, drag & drop, columnas, tarjetas
════════════════════════════════════════════════════ */

let dragTareaId = null;
let dragColOrigenId = null;
let placeholder = null;

/* ── SELECTORES ── */
async function cargarSelectores() {
  if (!S) return;
  try {
    const ps = await api("GET", "/proyectos/");
    const opts =
      '<option value="">— Selecciona un proyecto —</option>' +
      ps.map((p) => `<option value="${p.id}">${p.nombre}</option>`).join("");
    ["selPT", "selTareasProy", "selReporteProy", "selHistProy"].forEach(
      (id) => {
        const el = document.getElementById(id);
        if (!el) return;
        // Guardar valor seleccionado antes de reemplazar opciones
        const valorAnterior = el.value;
        el.innerHTML = opts;
        // Restaurar solo si el proyecto sigue existiendo en la lista
        if (valorAnterior && ps.some((p) => p.id === valorAnterior)) {
          el.value = valorAnterior;
        } else {
          // No restaurar — proyecto ya no existe o no hay selección válida
          el.value = "";
        }
      },
    );
  } catch (_) {}
}

function irTablero(id, nombre) {
  proyActualId = id;
  mostrarPantalla("tablero");
  setTimeout(() => {
    const sel = document.getElementById("selPT");
    const bc = document.getElementById("tBreadcrumb");
    if (sel) sel.value = id;
    if (bc) bc.textContent = nombre;
    cargarTablero(id);
  }, 0);
}

/* ── CARGA DEL TABLERO ── */
async function cargarTablero(proyId) {
  if (!proyId) return;
  // Verificar que el proyecto seleccionado en el UI coincide con el que se pide cargar
  const sel = document.getElementById("selPT");
  if (sel && sel.value && sel.value !== proyId) {
    // El usuario cambió el selector antes de que terminara la carga anterior — abortar
    return;
  }
  proyActualId = proyId;
  const board = document.getElementById("kanbanBoard");
  board.innerHTML =
    '<div class="vacío" style="width:100%"><span class="spinner"></span> Cargando...</div>';
  try {
    // Cargar tableros y miembros en paralelo
    const [tableros, miembros] = await Promise.all([
      api("GET", `/proyectos/${proyId}/tableros`),
      api("GET", `/proyectos/${proyId}/miembros`).catch(() => []),
    ]);
    miembrosActuales = miembros;
    if (!tableros.length) {
      board.innerHTML =
        '<div class="vacío" style="width:100%">Sin tableros</div>';
      return;
    }
    colsActuales = tableros[0].columnas || [];
    const bc = document.getElementById("tBreadcrumb");
    if (bc) bc.textContent = tableros[0].nombre;

    const cols = await Promise.all(
      colsActuales.map(async (col) => {
        const tareas = await api("GET", `/columnas/${col.id}/tareas`);
        return { ...col, tareas };
      }),
    );

    board.innerHTML =
      cols
        .map(
          (c) => `
      <div class="k-col" id="col-${c.id}" data-col-id="${c.id}">
        <div class="k-col-head">
          <div class="k-col-title">
            <div class="k-col-dot" style="background:${colColor(c.nombre)}"></div>
            ${c.nombre}
          </div>
          <div style="display:flex;align-items:center;gap:6px">
            <span class="k-col-cnt" id="cnt-${c.id}">${c.tareas.length}${c.limiteWip ? "/" + c.limiteWip : ""}</span>
            <button class="btn btn-ghost btn-xs" style="color:var(--t3)"
              onclick="eliminarColumna('${c.id}')" title="Eliminar columna"><i class="ph ph-x"></i></button>
          </div>
        </div>
        ${c.limiteWip ? `<div class="k-wip">WIP: ${c.tareas.length}/${c.limiteWip}</div>` : ""}
        <div class="k-cards" id="cards-${c.id}" data-col-id="${c.id}">
          ${c.tareas.map((t) => tarjeta(t)).join("")}
        </div>
        <div class="k-add" onclick="abrirModalTareaCol('${c.id}')"><i class='ph ph-plus'></i> Agregar tarea</div>
      </div>`,
        )
        .join("") +
      `<div class="k-col-nueva" onclick="agregarColumna()">
        <span class="k-col-nueva-icon"><i class='ph ph-plus-circle'></i></span>
        <span>Nueva columna</span>
      </div>`;

    iniciarDragDrop();
  } catch (e) {
    board.innerHTML = `<div class="vacío" style="width:100%">Error: ${e.message}</div>`;
  }
}

function colColor(nombre) {
  const n = nombre.toLowerCase();
  if (n.includes("hacer") || n.includes("backlog")) return "var(--txt3)";
  if (n.includes("progreso") || n.includes("proceso")) return "var(--acento)";
  if (n.includes("revisi")) return "var(--ambar)";
  if (n.includes("complet") || n.includes("listo")) return "var(--verde)";
  return "var(--cyan)";
}

function tarjeta(t) {
  const resps = (t.responsables || [])
    .slice(0, 3)
    .map((id) => {
      const m = miembrosActuales.find((m) => m.id === id);
      return `<div class="avatar avatar-sm" title="${m?.nombre || id}">${inic(m?.nombre || "?")}</div>`;
    })
    .join("");
  return `<div class="k-card" draggable="true" data-tarea-id="${t.id}" data-col-id="${t.columnaId}">
    <div class="k-card-tags">
      <div class="prio ${colPrio(t.prioridad)}"></div>
      ${badgeTipo(t.tipo)}
      ${t.estaVencida ? '<span class="badge br">Vencida</span>' : ""}
    </div>
    <div class="k-card-title">${t.titulo}</div>
    <div class="k-card-meta">
      <span class="k-card-id">#${t.id.slice(-6)}</span>
      <div class="flex" style="gap:4px">
        <div class="avatar-group">${resps}</div>
        <button class="btn btn-ghost btn-xs" onclick="abrirAsignar('${t.id}')" title="Asignar"><i class="ph ph-user-plus"></i></button>
        <button class="btn btn-ghost btn-xs" onclick="clonarTarea('${t.id}')" title="Clonar"><i class="ph ph-copy"></i></button>
        <button class="btn btn-red btn-xs" onclick="eliminarTarea('${t.id}')" title="Eliminar"><i class="ph ph-trash"></i></button>
      </div>
    </div>
  </div>`;
}

/* ── DRAG & DROP ── */
function iniciarDragDrop() {
  document.querySelectorAll(".k-cards").forEach((zona) => {
    zona.addEventListener("dragover", onDragOver);
    zona.addEventListener("dragenter", onDragEnter);
    zona.addEventListener("dragleave", onDragLeave);
    zona.addEventListener("drop", onDrop);
  });
  document.querySelectorAll(".k-card").forEach((card) => {
    card.addEventListener("dragstart", onDragStart);
    card.addEventListener("dragend", onDragEnd);
  });
}

function onDragStart(e) {
  dragTareaId = this.dataset.tareaId;
  dragColOrigenId = this.dataset.colId;
  this.classList.add("dragging");
  e.dataTransfer.effectAllowed = "move";
  e.dataTransfer.setData("text/plain", dragTareaId);
  placeholder = document.createElement("div");
  placeholder.className = "k-card drag-placeholder";
  placeholder.style.height = this.offsetHeight + "px";
}

function onDragEnd() {
  this.classList.remove("dragging");
  placeholder?.remove();
  placeholder = null;
  document
    .querySelectorAll(".k-col")
    .forEach((c) => c.classList.remove("drag-over"));
}

function onDragEnter(e) {
  e.preventDefault();
  e.currentTarget.closest(".k-col")?.classList.add("drag-over");
}

function onDragLeave(e) {
  const zona = e.currentTarget;
  if (!zona.contains(e.relatedTarget)) {
    zona.closest(".k-col")?.classList.remove("drag-over");
  }
}

function onDragOver(e) {
  e.preventDefault();
  e.dataTransfer.dropEffect = "move";
  if (!placeholder) return;
  const zona = e.currentTarget;
  const cardDebajo = obtenerCardDebajo(zona, e.clientY);
  if (cardDebajo) zona.insertBefore(placeholder, cardDebajo);
  else zona.appendChild(placeholder);
}

async function onDrop(e) {
  e.preventDefault();
  const zona = e.currentTarget;
  const colDestinoId = zona.dataset.colId;
  zona.closest(".k-col")?.classList.remove("drag-over");
  placeholder?.remove();
  if (!dragTareaId || colDestinoId === dragColOrigenId) return;

  const cardEl = document.querySelector(`[data-tarea-id="${dragTareaId}"]`);
  if (cardEl) {
    cardEl.dataset.colId = colDestinoId;
    zona.appendChild(cardEl);
    actualizarContadores(dragColOrigenId, colDestinoId);
  }
  try {
    await api("POST", `/tareas/${dragTareaId}/mover`, {
      columnaIdDestino: colDestinoId,
    });
    toast("Tarea movida");
  } catch (err) {
    const colOrigen = document.getElementById(`cards-${dragColOrigenId}`);
    if (cardEl && colOrigen) {
      cardEl.dataset.colId = dragColOrigenId;
      colOrigen.appendChild(cardEl);
      actualizarContadores(colDestinoId, dragColOrigenId);
    }
    toast(err.message, "err");
  }
}

function actualizarContadores(colOrigenId, colDestinoId) {
  [colOrigenId, colDestinoId].forEach((id) => {
    const zona = document.getElementById(`cards-${id}`);
    const cnt = document.getElementById(`cnt-${id}`);
    if (!zona || !cnt) return;
    const total = zona.querySelectorAll(
      ".k-card:not(.drag-placeholder)",
    ).length;
    const match = cnt.textContent.match(/\/\d+/);
    cnt.textContent = total + (match ? match[0] : "");
  });
}

function obtenerCardDebajo(zona, y) {
  const cards = [
    ...zona.querySelectorAll(".k-card:not(.dragging):not(.drag-placeholder)"),
  ];
  return cards.reduce((mejor, card) => {
    const rect = card.getBoundingClientRect();
    const offset = y - (rect.top + rect.height / 2);
    if (offset < 0 && offset > (mejor?.offset ?? -Infinity)) {
      return { offset, elemento: card };
    }
    return mejor;
  }, null)?.elemento;
}

/* ── COLUMNAS ── */
async function eliminarColumna(colId) {
  if (!confirm("La columna debe estar vacía para eliminarla. ¿Continuar?"))
    return;
  try {
    await api("DELETE", `/columnas/${colId}`);
    toast("Columna eliminada");
    cargarTablero(proyActualId);
  } catch (e) {
    toast(e.message, "err");
  }
}

function agregarColumna() {
  if (!proyActualId) {
    toast("Primero selecciona un proyecto", "err");
    return;
  }
  document.getElementById("colNombre").value = "";
  document.getElementById("colError").textContent = "";
  abrirModal("mColumna");
  setTimeout(() => document.getElementById("colNombre").focus(), 100);
}

async function confirmarAgregarColumna() {
  const nombre = document.getElementById("colNombre").value.trim();
  document.getElementById("colError").textContent = "";
  if (!nombre) {
    document.getElementById("colError").textContent =
      "El nombre es obligatorio";
    return;
  }
  try {
    const tableros = await api("GET", `/proyectos/${proyActualId}/tableros`);
    if (!tableros.length) throw new Error("No hay tablero en este proyecto");
    await api("POST", `/tableros/${tableros[0].id}/columnas`, { nombre });
    cerrarModal("mColumna");
    toast("Columna creada");
    cargarTablero(proyActualId);
  } catch (e) {
    document.getElementById("colError").textContent = e.message;
  }
}
