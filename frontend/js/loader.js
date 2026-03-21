/* TaskFlow — loader.js */
const PAGINAS_HTML = {
  login: `<div class="login-overlay" id="loginOverlay">
  <div class="login-split">
    <div class="login-brand">
      <div class="login-brand-logo">
        <div class="login-brand-icon">TF</div>
        <span class="login-brand-name">TaskFlow</span>
      </div>
      <div class="login-brand-body">
        <div class="login-brand-title">Gestión ágil para<br>equipos que entregan</div>
        <div class="login-brand-desc">Organiza proyectos, asigna tareas y mantén el control con tableros Kanban en tiempo real.</div>
      </div>
      <div class="login-brand-pills">
        <div class="login-brand-pill"><i class="ph ph-kanban pico"></i> Kanban</div>
        <div class="login-brand-pill"><i class="ph ph-users pico"></i> Equipos</div>
        <div class="login-brand-pill"><i class="ph ph-chart-bar pico"></i> Reportes</div>
        <div class="login-brand-pill"><i class="ph ph-bell pico"></i> Notificaciones</div>
      </div>
    </div>
    <div class="login-form-panel">
      <div class="login-form-title">Iniciar sesión</div>
      <div class="login-form-sub">Ingresa tus credenciales para continuar</div>
      <div class="fg">
        <label class="flabel">Correo electrónico</label>
        <input class="finput" id="lEmail" type="email" placeholder="correo@empresa.com" autocomplete="email">
      </div>
      <div class="fg">
        <label class="flabel">Contraseña</label>
        <div style="position:relative">
          <input class="finput" id="lPass" type="password" placeholder="••••••••" autocomplete="current-password" style="padding-right:40px">
          <button onclick="toggleVerPass()" tabindex="-1" id="btnVerPass"
            style="position:absolute;right:10px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:var(--t3);padding:4px;display:flex;align-items:center">
            <i class="ph ph-eye" style="font-size:16px"></i>
          </button>
        </div>
        <div class="ferror" id="lError"></div>
      </div>
      <button class="btn btn-primary btn-w" id="btnLogin" onclick="iniciarSesion()" style="margin-top:8px">
        <i class="ph ph-sign-in"></i> Iniciar sesión
      </button>
      <div class="login-divider">roles del sistema</div>
      <div style="display:flex;gap:7px;justify-content:center">
        <span class="badge bi">Admin</span>
        <span class="badge bb">Project Manager</span>
        <span class="badge bg">Developer</span>
      </div>
    </div>
  </div>
</div>
<div class="pantalla activa" id="pantalla-login" style="display:none"></div>`,
  dashboard: `<div class="pantalla" id="pantalla-dashboard">
  <div class="dash-wrap">

    <!-- Header -->
    <div class="dash-header">
      <div>
        <div class="dash-title" id="dashSaludo">Dashboard</div>
        <div class="dash-sub">
          <i class="ph-fill ph-circle" style="font-size:8px;color:var(--green)"></i>
          En tiempo real &nbsp;·&nbsp; <span id="dashFecha"></span>
        </div>
      </div>
      <div class="flex" style="gap:8px">
        <select class="fselect" id="selDashProy" style="width:200px;padding:6px 10px;font-size:12px" onchange="actualizarDashboardProy(this.value)">
          <option value="">— Todos los proyectos —</option>
        </select>
        <button class="btn btn-outline btn-sm" onclick="refrescarDashboard()" title="Actualizar datos">
          <i class="ph ph-arrows-clockwise"></i>
        </button>
        <div id="dashAcciones"></div>
      </div>
    </div>

    <!-- KPI Cards grandes -->
    <div class="kpi-grid">
      <div class="kpi-card" style="--kc:108,99,255">
        <div class="kpi-icon" style="background:rgba(108,99,255,.15);color:#8b83ff">
          <i class="ph ph-folder-open"></i>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">Proyectos activos</div>
          <div class="kpi-value" id="stProy">—</div>
          <div class="kpi-sub" id="stProySub">—</div>
        </div>
        <div class="kpi-glow" style="background:radial-gradient(circle at 80% 50%,rgba(108,99,255,.18) 0%,transparent 65%)"></div>
      </div>

      <div class="kpi-card" style="--kc:52,211,153">
        <div class="kpi-icon" style="background:rgba(52,211,153,.15);color:#34d399">
          <i class="ph ph-check-square"></i>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">Tareas totales</div>
          <div class="kpi-value" id="stTareas">—</div>
          <div class="kpi-sub" id="stTareasSub">en el proyecto</div>
        </div>
        <div class="kpi-glow" style="background:radial-gradient(circle at 80% 50%,rgba(52,211,153,.15) 0%,transparent 65%)"></div>
      </div>

      <div class="kpi-card" style="--kc:248,113,113">
        <div class="kpi-icon" style="background:rgba(248,113,113,.15);color:#f87171">
          <i class="ph ph-warning-circle"></i>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">Tareas vencidas</div>
          <div class="kpi-value" id="stVencidas" style="color:#f87171">—</div>
          <div class="kpi-sub" id="stVencidasSub">requieren atención</div>
        </div>
        <div class="kpi-glow" style="background:radial-gradient(circle at 80% 50%,rgba(248,113,113,.15) 0%,transparent 65%)"></div>
      </div>

      <div class="kpi-card" style="--kc:251,191,36" id="statNotifWrap">
        <div class="kpi-icon" style="background:rgba(251,191,36,.15);color:#fbbf24">
          <i class="ph ph-bell-ringing"></i>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">Sin leer</div>
          <div class="kpi-value" id="stNotif">—</div>
          <div class="kpi-sub">notificaciones</div>
        </div>
        <div class="kpi-glow" style="background:radial-gradient(circle at 80% 50%,rgba(251,191,36,.15) 0%,transparent 65%)"></div>
      </div>

      <div class="kpi-card" style="--kc:96,165,250;display:none" id="statUsuariosWrap">
        <div class="kpi-icon" style="background:rgba(96,165,250,.15);color:#60a5fa">
          <i class="ph ph-users"></i>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">Usuarios</div>
          <div class="kpi-value" id="stUsers">—</div>
          <div class="kpi-sub">en el sistema</div>
        </div>
        <div class="kpi-glow" style="background:radial-gradient(circle at 80% 50%,rgba(96,165,250,.15) 0%,transparent 65%)"></div>
      </div>
    </div>

    <!-- Fila principal: donut grande + velocidad -->
    <div class="dash-row-main">
      <div class="card dash-chart-lg">
        <div class="chart-header">
          <div>
            <div class="chart-title"><i class="ph ph-chart-donut" style="color:var(--a)"></i> Estado del proyecto</div>
            <div class="chart-sub">Distribución de tareas por columna</div>
          </div>
        </div>
        <div id="chartColumnas" style="height:280px"></div>
      </div>

      <div class="card dash-chart-md">
        <div class="chart-header">
          <div>
            <div class="chart-title"><i class="ph ph-trend-up" style="color:var(--green)"></i> Velocidad del equipo</div>
            <div class="chart-sub">Tareas creadas por semana</div>
          </div>
        </div>
        <div id="chartVelocidad" style="height:280px"></div>
      </div>
    </div>

    <!-- Fila secundaria: prioridad + tipo -->
    <div class="dash-row-2">
      <div class="card">
        <div class="chart-header">
          <div class="chart-title"><i class="ph ph-chart-bar-horizontal" style="color:var(--amber)"></i> Por prioridad</div>
        </div>
        <div id="chartPrioridad" style="height:200px"></div>
      </div>
      <div class="card">
        <div class="chart-header">
          <div class="chart-title"><i class="ph ph-tag" style="color:var(--blue)"></i> Por tipo</div>
        </div>
        <div id="chartTipo" style="height:200px"></div>
      </div>
      <div class="card">
        <div class="chart-header">
          <div class="chart-title"><i class="ph ph-users-three" style="color:var(--purple)"></i> Carga del equipo</div>
        </div>
        <div id="chartEquipo" style="height:200px"></div>
      </div>
    </div>

    <!-- Proyectos recientes -->
    <div class="card" style="margin-bottom:24px">
      <div class="chart-header" style="margin-bottom:16px">
        <div>
          <div class="chart-title"><i class="ph ph-folder-simple-star" style="color:var(--a)"></i> Proyectos recientes</div>
          <div class="chart-sub">Últimos proyectos con actividad</div>
        </div>
        <div id="dashAccionesProy"></div>
      </div>
      <div id="dashProyectos" class="vacío">Cargando...</div>
    </div>

  </div>
</div>
`,
  proyectos: `<div class="pantalla" id="pantalla-proyectos">
  <div class="page-wrap">
    <div class="page-head">
      <div><div class="page-title">Proyectos</div><div class="page-desc">Gestiona y organiza tus proyectos</div></div>
      <div class="flex" id="proyAcciones"></div>
    </div>
    <div class="card"><div class="card-t"><i class="ph ph-list"></i> Listado</div><div id="listaProyectos" class="vacío">Cargando...</div></div>
  </div>
</div>`,
  tablero: `<div class="pantalla" id="pantalla-tablero">
  <div class="kanban-barra">
    <select class="fselect" id="selPT" style="width:220px;padding:6px 10px" onchange="cargarTablero(this.value)">
      <option value="">— Selecciona un proyecto —</option>
    </select>
    <span id="tBreadcrumb" class="txt3"></span>
    <div style="margin-left:auto;display:flex;gap:7px">
      <button class="btn btn-outline btn-sm" onclick="agregarColumna()">
        <i class="ph ph-columns-plus-right"></i> Columna
      </button>
      <button class="btn btn-primary btn-sm" onclick="abrirModalTarea()">
        <i class="ph ph-plus"></i> Tarea
      </button>
    </div>
  </div>
  <div class="kanban-shell" id="kanbanBoard">
    <div class="vacío" style="width:100%">Selecciona un proyecto para ver el tablero</div>
  </div>
</div>`,
  tareas: `<div class="pantalla" id="pantalla-tareas">
  <div class="page-wrap">
    <div class="page-head">
      <div><div class="page-title">Tareas</div><div class="page-desc">Gestión y seguimiento de tareas</div></div>
      <div class="flex">
        <select class="fselect" id="selTareasProy" style="width:200px;padding:6px 10px" onchange="cargarTareasPaginadas(this.value,1)">
          <option value="">— Proyecto —</option>
        </select>
        <button class="btn btn-primary btn-sm" onclick="abrirModalTarea()">
          <i class="ph ph-plus"></i> Nueva
        </button>
      </div>
    </div>
    <div class="card">
      <div class="tabla-wrap">
        <table>
          <thead><tr><th>Título</th><th>Tipo</th><th>Prioridad</th><th>Responsables</th><th>Estado</th><th>Acciones</th></tr></thead>
          <tbody id="tbTareas"><tr><td colspan="6" class="vacío">Selecciona un proyecto para ver las tareas</td></tr></tbody>
        </table>
      </div>
      <div id="pagTareas"></div>
    </div>
  </div>
</div>`,
  usuarios: `<div class="pantalla" id="pantalla-usuarios">
  <div class="page-wrap">
    <div class="page-head">
      <div><div class="page-title">Usuarios</div><div class="page-desc">Gestión de cuentas del sistema</div></div>
      <span class="badge bi"><i class="ph ph-lock-simple"></i> Solo Admin</span>
    </div>
    <div class="card">
      <div class="tabla-wrap">
        <table>
          <thead><tr><th>Nombre</th><th>Email</th><th>Rol</th><th>Último acceso</th><th>Estado</th><th>Acciones</th></tr></thead>
          <tbody id="tbUsuarios"><tr><td colspan="6" class="vacío">Cargando...</td></tr></tbody>
        </table>
      </div>
    </div>
  </div>
</div>`,
  registro: `<div class="pantalla" id="pantalla-registro">
  <div class="registro-wrap">

    <div class="registro-left">
      <div class="registro-brand-ico"><i class="ph ph-user-plus"></i></div>
      <div class="registro-brand-title">Nuevo usuario</div>
      <div class="registro-brand-desc">Crea una cuenta para que el miembro pueda acceder al sistema con el rol asignado.</div>
      <div class="sep"></div>
      <div class="registro-roles">
        <div class="registro-rol-item">
          <div class="registro-rol-ico" style="background:var(--redbg);color:var(--red)"><i class="ph ph-shield-star"></i></div>
          <div>
            <div class="registro-rol-nombre">Admin</div>
            <div class="registro-rol-desc">Acceso total al sistema</div>
          </div>
        </div>
        <div class="registro-rol-item">
          <div class="registro-rol-ico" style="background:var(--bluebg);color:var(--blue)"><i class="ph ph-briefcase"></i></div>
          <div>
            <div class="registro-rol-nombre">Project Manager</div>
            <div class="registro-rol-desc">Gestiona proyectos y equipos</div>
          </div>
        </div>
        <div class="registro-rol-item">
          <div class="registro-rol-ico" style="background:var(--greenbg);color:var(--green)"><i class="ph ph-code"></i></div>
          <div>
            <div class="registro-rol-nombre">Developer</div>
            <div class="registro-rol-desc">Trabaja en tareas asignadas</div>
          </div>
        </div>
      </div>
    </div>

    <div class="registro-right">
      <div class="card registro-form-card">
        <div class="perfil-section-title" style="margin-bottom:20px">
          <i class="ph ph-identification-card" style="color:var(--a)"></i> Datos del nuevo usuario
        </div>

        <div class="fg">
          <label class="flabel">Nombre completo</label>
          <div style="position:relative">
            <input class="finput" id="rNombre" placeholder="Ej: María García" style="padding-left:36px">
            <i class="ph ph-user" style="position:absolute;left:11px;top:50%;transform:translateY(-50%);color:var(--t3);font-size:15px"></i>
          </div>
        </div>

        <div class="fg">
          <label class="flabel">Correo electrónico</label>
          <div style="position:relative">
            <input class="finput" id="rEmail" type="email" placeholder="correo@empresa.com" style="padding-left:36px">
            <i class="ph ph-envelope" style="position:absolute;left:11px;top:50%;transform:translateY(-50%);color:var(--t3);font-size:15px"></i>
          </div>
        </div>

        <div class="fg">
          <label class="flabel">Contraseña inicial</label>
          <div style="position:relative">
            <input class="finput" id="rPass" type="password" placeholder="Mínimo 6 caracteres" style="padding-left:36px;padding-right:40px">
            <i class="ph ph-lock-key" style="position:absolute;left:11px;top:50%;transform:translateY(-50%);color:var(--t3);font-size:15px"></i>
            <button onclick="toggleVerPassReg()" tabindex="-1"
              style="position:absolute;right:10px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:var(--t3);padding:4px;display:flex;align-items:center">
              <i class="ph ph-eye" id="iconoVerPassReg" style="font-size:15px"></i>
            </button>
          </div>
        </div>

        <div class="fg">
          <label class="flabel">Rol del usuario</label>
          <div class="registro-rol-selector" id="rRolSelector">
            <div class="registro-rol-opt activo" data-val="DEVELOPER" onclick="seleccionarRol(this)">
              <i class="ph ph-code"></i>
              <span>Developer</span>
            </div>
            <div class="registro-rol-opt" data-val="PROJECT_MANAGER" onclick="seleccionarRol(this)">
              <i class="ph ph-briefcase"></i>
              <span>PM</span>
            </div>
            <div class="registro-rol-opt" data-val="ADMIN" onclick="seleccionarRol(this)">
              <i class="ph ph-shield-star"></i>
              <span>Admin</span>
            </div>
          </div>
          <input type="hidden" id="rRol" value="DEVELOPER">
        </div>

        <div class="ferror" id="rError"></div>

        <button class="btn btn-primary btn-w" onclick="crearUsuario()" style="height:40px;font-size:14px">
          <i class="ph ph-user-plus"></i> Crear usuario
        </button>
      </div>
    </div>
  </div>
</div>
`,
  reportes: `<div class="pantalla" id="pantalla-reportes">
  <div class="page-wrap">
    <div class="page-head">
      <div><div class="page-title">Reportes y estadísticas</div><div class="page-desc">Métricas y seguimiento del proyecto</div></div>
      <select class="fselect" id="selReporteProy" style="width:220px;padding:6px 10px" onchange="cargarReporte(this.value)">
        <option value="">— Selecciona un proyecto —</option>
      </select>
    </div>
    <div class="htabs" id="tabsReporte">
      <button class="htab activo" onclick="cambiarTabReporte('metricas',this)"><i class="ph ph-chart-pie"></i> Métricas</button>
      <button class="htab" onclick="cambiarTabReporte('sprint',this)"><i class="ph ph-lightning"></i> Sprint</button>
      <button class="htab" onclick="cambiarTabReporte('equipo',this)"><i class="ph ph-users-three"></i> Equipo</button>
      <button class="htab" id="tabAuditGlobal" onclick="cambiarTabReporte('auditoria_global',this)" style="display:none"><i class="ph ph-shield-check"></i> Auditoría global</button>
      <button class="htab" id="tabRetencion" onclick="cambiarTabReporte('retencion',this)" style="display:none"><i class="ph ph-archive"></i> Retención</button>
    </div>
    <div class="hpanel activo" id="rpanel-metricas">
      <div class="stats-row">
        <div class="stat" style="--g:rgba(108,99,255,.3)"><div class="stat-n">Total tareas</div><div class="stat-v" id="rTotal">—</div></div>
        <div class="stat" style="--g:rgba(248,113,113,.3)"><div class="stat-n">Vencidas</div><div class="stat-v" id="rVenc" style="color:var(--red)">—</div></div>
        <div class="stat" style="--g:rgba(52,211,153,.3)"><div class="stat-n">Progreso</div><div class="stat-v" id="rProg">—</div></div>
      </div>
      <div class="card"><div class="card-t"><i class="ph ph-list-bullets"></i> Distribución por columna</div><div id="rDist" class="vacío">Selecciona un proyecto</div></div>
    </div>
    <div class="hpanel" id="rpanel-sprint">
      <div class="card">
        <div class="card-t"><i class="ph ph-lightning"></i> Reporte de sprint</div>
        <div class="flex" style="gap:8px;margin-bottom:16px">
          <input class="finput" id="sprintNombre" placeholder="Nombre del sprint (ej: Sprint 1, Q1 2026...)" style="flex:1">
          <button class="btn btn-primary btn-sm" onclick="generarReporteSprint()"><i class="ph ph-play"></i> Generar</button>
        </div>
        <div id="contenidoSprint" class="vacío">Selecciona un proyecto e ingresa el nombre del sprint</div>
      </div>
    </div>
    <div class="hpanel" id="rpanel-equipo">
      <div class="card"><div class="card-t"><i class="ph ph-users-three"></i> Estadísticas del equipo</div><div id="statsEquipo" class="vacío">Selecciona un proyecto</div></div>
    </div>
    <div class="hpanel" id="rpanel-auditoria_global">
      <div class="card"><div class="card-t"><i class="ph ph-shield-check"></i> Auditoría global del sistema</div><div id="listaAuditoriaGlobal" class="vacío">Cargando...</div></div>
    </div>
    <div class="hpanel" id="rpanel-retencion">
      <div class="card">
        <div class="card-t"><i class="ph ph-archive"></i> Política de retención de logs</div>
        <div class="fg" style="max-width:320px"><label class="flabel">Días de retención</label><input class="finput" id="diasRetencion" type="number" value="90" min="7" max="365"></div>
        <div class="fg" style="max-width:320px">
          <label class="flabel">Nivel mínimo a conservar</label>
          <select class="fselect" id="nivelRetencion">
            <option value="todos">Todos los registros</option>
            <option value="error">Solo errores</option>
            <option value="auditoria">Solo auditoría</option>
          </select>
        </div>
        <button class="btn btn-primary btn-sm" onclick="aplicarPoliticaRetencion()"><i class="ph ph-check"></i> Aplicar política</button>
        <div id="retencionMensaje" class="txt3" style="margin-top:12px"></div>
      </div>
    </div>
  </div>
</div>`,
  historial: `<div class="pantalla" id="pantalla-historial">
  <div class="page-wrap">
    <div class="page-head">
      <div><div class="page-title">Historial y auditoría</div><div class="page-desc">Registro de cambios del proyecto</div></div>
      <select class="fselect" id="selHistProy" style="width:220px;padding:6px 10px" onchange="cargarHistorial(this.value)">
        <option value="">— Selecciona un proyecto —</option>
      </select>
    </div>
    <div class="htabs" id="tabsHistorial">
      <button class="htab activo" onclick="cambiarTabHist('auditoria',this)"><i class="ph ph-clock-clockwise"></i> Auditoría</button>
      <button class="htab" onclick="cambiarTabHist('tarea',this)"><i class="ph ph-file-text"></i> Por tarea</button>
      <button class="htab" onclick="cambiarTabHist('buscar',this)"><i class="ph ph-magnifying-glass"></i> Buscar</button>
      <button class="htab" onclick="cambiarTabHist('completadas',this)"><i class="ph ph-check-circle"></i> Completadas</button>
    </div>
    <div class="hpanel activo" id="hpanel-auditoria">
      <div class="card"><div class="card-t"><i class="ph ph-activity"></i> Actividad reciente</div><div id="listaHist" class="vacío">Selecciona un proyecto</div></div>
    </div>
    <div class="hpanel" id="hpanel-tarea">
      <div class="card">
        <div class="card-t"><i class="ph ph-file-magnifying-glass"></i> Historial de una tarea</div>
        <div class="flex" style="gap:8px;margin-bottom:16px">
          <input class="finput" id="histTareaId" placeholder="ID de tarea (últimos 6 caracteres)..." style="flex:1">
          <button class="btn btn-primary btn-sm" onclick="cargarHistorialTarea()"><i class="ph ph-magnifying-glass"></i> Ver</button>
        </div>
        <div id="listaHistTarea" class="vacío">Ingresa el ID de una tarea</div>
        <div id="undoZona" style="display:none;margin-top:16px;padding-top:16px;border-top:1px solid var(--b1)">
          <div class="flex-between">
            <span class="txt2">Último cambio registrado</span>
            <button class="btn btn-outline btn-sm" onclick="deshacerUltimoCambio()" style="border-color:var(--amber);color:var(--amber)">
              <i class="ph ph-arrow-counter-clockwise"></i> Deshacer
            </button>
          </div>
          <div id="undoDetalle" class="txt3" style="margin-top:6px"></div>
        </div>
      </div>
    </div>
    <div class="hpanel" id="hpanel-buscar">
      <div class="card">
        <div class="card-t"><i class="ph ph-funnel"></i> Buscar y filtrar tareas</div>
        <div class="filtro-barra">
          <input class="finput" id="fTexto" placeholder="Título..." style="flex:2;min-width:140px">
          <select class="fselect" id="fPrioridad" style="width:120px">
            <option value="">Prioridad</option>
            <option value="BAJA">Baja</option><option value="MEDIA">Media</option>
            <option value="ALTA">Alta</option><option value="URGENTE">Urgente</option>
          </select>
          <select class="fselect" id="fTipo" style="width:120px">
            <option value="">Tipo</option>
            <option value="TASK">Task</option><option value="BUG">Bug</option>
            <option value="FEATURE">Feature</option><option value="IMPROVEMENT">Improvement</option>
          </select>
          <button class="btn btn-primary btn-sm" onclick="buscarTareas()"><i class="ph ph-magnifying-glass"></i> Buscar</button>
          <button class="btn btn-ghost btn-sm" onclick="limpiarFiltros()"><i class="ph ph-x"></i></button>
        </div>
        <div class="tabla-wrap">
          <table>
            <thead><tr><th>Título</th><th>Tipo</th><th>Prioridad</th><th>Columna</th><th>Estado</th></tr></thead>
            <tbody id="tbBusqueda"><tr><td colspan="5" class="vacío">Aplica un filtro para buscar</td></tr></tbody>
          </table>
        </div>
      </div>
    </div>
    <div class="hpanel" id="hpanel-completadas">
      <div class="card"><div class="card-t"><i class="ph ph-check-circle"></i> Mis tareas completadas</div><div id="listaCompletadas" class="vacío">Selecciona un proyecto primero</div></div>
    </div>
  </div>
</div>
`,
  notificaciones: `<div class="pantalla" id="pantalla-notificaciones">
  <div class="page-wrap">
    <div class="page-head">
      <div><div class="page-title">Notificaciones</div><div class="page-desc" id="notifDesc">Alertas y avisos del sistema</div></div>
      <div class="flex" style="gap:8px">
        <button class="btn btn-outline btn-sm" id="btnMarcarLeidas" onclick="marcarTodasLeidas()" style="display:none">
          <i class="ph ph-checks"></i> Marcar todas leídas
        </button>
      </div>
    </div>
    <div id="panelAdminNotif" style="display:none">
      <div class="card">
        <div class="flex-between" style="margin-bottom:14px">
          <div class="card-t" style="margin-bottom:0"><i class="ph ph-globe"></i> Todas las notificaciones del sistema</div>
          <span class="badge bi"><i class="ph ph-shield-star"></i> Vista Admin</span>
        </div>
        <div class="tabla-wrap">
          <table>
            <thead><tr><th>Mensaje</th><th>Tipo</th><th>Destinatario</th><th>Estado</th><th>Fecha</th></tr></thead>
            <tbody id="tbTodasNotif"><tr><td colspan="5" class="vacío">Cargando...</td></tr></tbody>
          </table>
        </div>
      </div>
    </div>
    <div id="panelMisNotif" style="display:none">
      <div class="card mb16"><div class="card-t"><i class="ph ph-bell-simple"></i> Mis notificaciones</div><div id="listaNotifc" class="vacío">Cargando...</div></div>
      <div class="card">
        <div class="card-t"><i class="ph ph-sliders"></i> Preferencias</div>
        <div id="prefsNotif"></div>
        <div style="margin-top:16px"><button class="btn btn-primary btn-sm" onclick="guardarPrefs()"><i class="ph ph-floppy-disk"></i> Guardar preferencias</button></div>
      </div>
    </div>
  </div>
</div>`,
  perfil: `<div class="pantalla" id="pantalla-perfil">
  <div class="perfil-wrap">

    <!-- Columna izquierda: avatar + info -->
    <div class="perfil-sidebar">
      <div class="card perfil-avatar-card">
        <label class="avatar-upload perfil-avatar-upload" title="Cambiar foto">
          <img id="perAvatarImg" src="" alt="avatar" class="perfil-foto" style="display:none">
          <div class="perfil-avatar-inic avatar" id="perAvatarInic">--</div>
          <div class="perfil-avatar-overlay">
            <i class="ph ph-camera"></i>
            <span>Cambiar foto</span>
          </div>
          <input type="file" id="perAvatarFile" accept="image/png,image/jpeg,image/webp" onchange="previsualizarAvatar(this)">
        </label>
        <div class="perfil-nombre" id="perNombreDisplay">—</div>
        <div class="flex" style="justify-content:center;gap:6px;margin:4px 0 8px">
          <span class="badge bm" id="perRolDisplay">—</span>
        </div>
        <div class="perfil-email" id="perEmailDisplay">—</div>
        <div class="sep"></div>
        <div class="perfil-stat-row">
          <div class="perfil-stat"><div class="perfil-stat-v" id="perStProyectos">—</div><div class="perfil-stat-l">Proyectos</div></div>
          <div class="perfil-stat-div"></div>
          <div class="perfil-stat"><div class="perfil-stat-v" id="perStTareas">—</div><div class="perfil-stat-l">Tareas</div></div>
          <div class="perfil-stat-div"></div>
          <div class="perfil-stat"><div class="perfil-stat-v" id="perStAcceso">—</div><div class="perfil-stat-l">Último acceso</div></div>
        </div>
      </div>
    </div>

    <!-- Columna derecha: formulario -->
    <div class="perfil-main">

      <div class="card mb16">
        <div class="perfil-section-title"><i class="ph ph-user-circle" style="color:var(--a)"></i> Información personal</div>
        <div class="frow">
          <div class="fg">
            <label class="flabel">Nombre completo</label>
            <input class="finput" id="perNombre" placeholder="Tu nombre completo">
          </div>
          <div class="fg">
            <label class="flabel">URL de avatar (opcional)</label>
            <input class="finput" id="perAvatarUrl" placeholder="https://..." oninput="previsualizarAvatarUrl(this.value)">
          </div>
        </div>
        <div class="fg">
          <label class="flabel">Descripción / Bio</label>
          <textarea class="ftextarea" id="perDesc" placeholder="Cuéntanos algo sobre ti..." style="min-height:80px"></textarea>
        </div>
        <div class="ferror" id="perError"></div>
        <div class="flex" style="justify-content:flex-end">
          <button class="btn btn-primary" onclick="guardarPerfil()">
            <i class="ph ph-floppy-disk"></i> Guardar cambios
          </button>
        </div>
      </div>

      <div class="card">
        <div class="perfil-section-title"><i class="ph ph-shield-check" style="color:var(--green)"></i> Seguridad de cuenta</div>
        <div class="perfil-info-row"><i class="ph ph-envelope" style="color:var(--t3)"></i><div><div class="perfil-info-label">Correo electrónico</div><div class="perfil-info-val" id="perEmailSeg">—</div></div></div>
        <div class="perfil-info-row"><i class="ph ph-identification-card" style="color:var(--t3)"></i><div><div class="perfil-info-label">Rol en el sistema</div><div class="perfil-info-val" id="perRolSeg">—</div></div></div>
        <div class="perfil-info-row"><i class="ph ph-clock" style="color:var(--t3)"></i><div><div class="perfil-info-label">Miembro desde</div><div class="perfil-info-val" id="perFechaReg">—</div></div></div>
        <div class="sep"></div>
        <div class="flex-between">
          <div class="txt2" style="font-size:12px">El cambio de contraseña y correo se gestionan desde el panel de administración.</div>
          <span class="badge bg"><i class="ph ph-lock-key"></i> Cuenta activa</span>
        </div>
      </div>

    </div>
  </div>
</div>
`,
};
function cargarPaginas() {
  Object.entries(PAGINAS_HTML).forEach(([n, h]) => {
    const s = document.getElementById(`slot-${n}`);
    if (s) s.innerHTML = h;
  });
}
document.addEventListener("DOMContentLoaded", () => {
  cargarPaginas();
  document.dispatchEvent(new Event("taskflow:ready"));
});
