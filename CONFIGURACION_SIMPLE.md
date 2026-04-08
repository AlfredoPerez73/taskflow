# 🔔 CONFIGURACIÓN SIMPLIFICADA - NOTIFICACIONES REALES (Solo Email)

## ✅ Versión Simple: 2 líneas en .env y listo!

Sin Twilio, sin SendGrid. Solo Gmail SMTP que probablemente ya tienes.

---

## 🚀 Setup (3 minutos)

### 1️⃣ Habilitar "Contraseña de aplicación" en Gmail

**Ir a:** https://myaccount.google.com/security

1. Busca "Verificación en 2 pasos" en el lado izquierdo
2. Si NO está activada, actívala
3. Una vez activada, ve a "Contraseñas de aplicación"
4. Aparecerá un selector: selecciona "Correo" y "Windows/Mac/Linux"
5. **Copia la contraseña generada** (16 caracteres)

### 2️⃣ Actualizar `.backend/.env` (Solo 2 líneas)

```env
MONGODB_URL=mongodb+srv://taskflowuser:Cuenta12345@taskflowcluster.2z5pvjf.mongodb.net/?appName=TaskFlowCluster
NOMBRE_BD=taskflow
CLAVE_SECRETA_JWT=taskflow_clave_super_secreta_2024_cambiar_en_produccion
ALGORITMO_JWT=HS256
MINUTOS_EXPIRACION_TOKEN=480
PUERTO=8000

# ──── EMAIL REAL (Gmail SMTP) ────
EMAIL_SMTP_USER=tu_email@gmail.com
EMAIL_SMTP_PASSWORD=aaaa bbbb cccc dddd
```

**Reemplaza:**

- `tu_email@gmail.com` por TU email de Gmail
- `aaaa bbbb cccc dddd` por la contraseña que copiaste en el paso 1

### 3️⃣ Listo! Sin instalaciones extra

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**No necesitas instalar nada más.** Python ya tiene SMTP.

---

## 🧪 Prueba que funciona

### Desde Postman o curl:

```bash
curl -X POST http://localhost:8000/api/v1/notificaciones/enviar-externo \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "canal": "email",
    "usuarioId": "user_id",
    "mensaje": "Hola! Este es un email REAL desde TaskFlow",
    "asunto": "Prueba"
  }'
```

**Deberías recibir el email en 5 segundos** ✉️

### O desde la interfaz:

1. Ir a **Tareas** → Crear una tarea
2. Ir a **Panel Admin** → **Notificaciones** → **Enviar externa**
3. Seleccionar canal: **Email**
4. Escribir mensaje
5. ¡Enviar!
6. Revisa tu email ✅

---

## 📊 Qué funciona

| Canal        | Status      | Detalles                   |
| ------------ | ----------- | -------------------------- |
| **Email**    | ✅ REAL     | Gmail SMTP, llega en 5 seg |
| **WhatsApp** | 📋 Simulado | En logs con emojis         |
| **SMS**      | 📋 Simulado | En logs con emojis         |

---

## 📝 Frontend + Backend

### Frontend verá:

1. Modal de "Enviar notificación externa"
2. Opciones: Email / WhatsApp / SMS / Ambos
3. Click en "Enviar"

### Backend:

- **Email**: ✅ REALMENTE enviado a tu bandeja
- **WhatsApp/SMS**:
  - En desarrollo: muestra log simulado
  - En producción (con Twilio): sería real

---

## 🔐 Seguridad

- La contraseña Gmail se guarda en `.env` (no en versión control)
- No se expone en logs
- Gmail requiere 2-factor para generar contraseña
- Es una contraseña **específica para esta aplicación**, no tu contraseña real

---

## ❌ Si no funciona

**Error: SMTPAuthenticationError**

- Verificar que copiaste bien la contraseña
- Verificar que 2-Step Verification esté **activada**
- Intentar generar una contraseña nueva

**Error: EMAIL_SMTP_USER no configurada**

- Verificar que editaste `.backend/.env`
- Reiniciar servidor: `python -m uvicorn main:app --reload`

---

## 🚀 Para Producción

Cuando quieras WhatsApp y SMS reales:

1. Instalar Twilio
2. Configurar credenciales
3. Cambiar código en `apis_externas.py`
4. (Es el mismo código pero con Twilio SDK)

**Ahora:** Solo pruebas con Email = rápido y simple ✅
