# 🔔 GUÍA DE CONFIGURACIÓN - NOTIFICACIONES REALES

## ✅ Cambios Realizados

Tu proyecto TaskFlow ahora tiene **notificaciones REALES**:

- ✓ **Emails**: Vía SendGrid o SMTP
- ✓ **WhatsApp**: Vía Twilio
- ✓ **SMS**: Vía Twilio

---

## 📋 Paso 1: Instalar dependencias

```bash
cd backend
pip install twilio sendgrid
# O simplemente:
pip install -r requirements.txt
```

---

## 🔐 Paso 2: Configurar Twilio (WhatsApp + SMS)

### 2.1 Crear cuenta en Twilio

1. Ir a https://www.twilio.com/
2. Crear una cuenta (pueden usar prueba gratuita)
3. Verificar número de teléfono
4. En Dashboard, obtener:
   - **Account SID**
   - **Auth Token**
   - **Twilio Phone Number** (para SMS)
   - **Twilio WhatsApp Number** (si quieres WhatsApp)

### 2.2 Actualizar `.backend/.env`

```env
# Twilio - WhatsApp y SMS
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_actual_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WHATSAPP_NUMBER=+1234567890
```

**Ejemplo completo de .env:**

```env
MONGODB_URL=mongodb+srv://taskflowuser:Cuenta12345@taskflowcluster.2z5pvjf.mongodb.net/?appName=TaskFlowCluster
NOMBRE_BD=taskflow
CLAVE_SECRETA_JWT=taskflow_clave_super_secreta_2024_cambiar_en_produccion
ALGORITMO_JWT=HS256
MINUTOS_EXPIRACION_TOKEN=480
PUERTO=8000

# Twilio - WhatsApp y SMS
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_actual_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WHATSAPP_NUMBER=+1234567890

# SendGrid - Email
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=noreply@taskflow.com
SENDGRID_FROM_NAME=TaskFlow
```

---

## 📧 Paso 3: Configurar SendGrid (Email)

### 3.1 Crear cuenta en SendGrid

1. Ir a https://sendgrid.com/
2. Crear cuenta gratuita (30 emails/día plan gratis, luego ilimitado)
3. En Settings → API Keys:
   - Crear una API Key
   - Guardarla (solo aparece una vez)

### 3.2 Actualizar `.backend/.env`

```env
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=noreply@taskflow.com
SENDGRID_FROM_NAME=TaskFlow
```

---

## 📱 Paso 3 (Alternativa): Configurar SMTP para Gmail (Fallback)

Si NO tienes SendGrid pero sí Gmail:

### 3.1 Habilitar "Contraseña de aplicación" en Gmail

1. Ir a https://myaccount.google.com/security
2. Activar autenticación de dos factores
3. Ir a "Contraseñas de aplicación"
4. Generar contraseña para "Correo" y "Windows/Mac/Linux"

### 3.2 Actualizar `.backend/.env`

```env
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=tu_contraseña_aplicacion
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

---

## 🧪 Paso 4: Probar

### Subir backend

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Probar endpoint en Postman o con curl

**Enviar Email:**

```bash
curl -X POST http://localhost:8000/api/v1/notificaciones/enviar-externo \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "canal": "email",
    "usuarioId": "user_id_aqui",
    "mensaje": "Prueba de email real desde TaskFlow",
    "asunto": "Notificación TaskFlow"
  }'
```

**Enviar SMS:**

```bash
curl -X POST http://localhost:8000/api/v1/notificaciones/enviar-externo \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "canal": "sms",
    "usuarioId": "user_id_aqui",
    "mensaje": "Este es un SMS de prueba desde TaskFlow"
  }'
```

**Enviar WhatsApp:**

```bash
curl -X POST http://localhost:8000/api/v1/notificaciones/enviar-externo \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "canal": "whatsapp",
    "usuarioId": "user_id_aqui",
    "mensaje": "Hola, esto es un mensaje de WhatsApp desde TaskFlow"
  }'
```

---

## 🎯 Comportamiento en Producción

### SendGrid + Email

- ✓ Envío profesional con plantillas HTML
- ✓ Tracking de entregas
- ✓ Rebotes automáticos

### Twilio + WhatsApp/SMS

- ✓ Números verificados
- ✓ Mensajes bidireccionales
- ✓ Webhooks para confirmación de entrega

### Fallback automático

Si falta una configuración:

- SendGrid no configurado → usa SMTP Gmail
- SMTP no configurado → log de error pero sigue funcionando
- Twilio no configurado → fallback simulado (en logs)

---

## 📊 Flujo en Frontend

El usuario verá:

1. **Panel de Subtareas** (📋 en tabla)
   - Crear/editar/eliminar subtareas
   - Marcar como completadas

2. **Modal de Notificación Externa** (solo PM/ADMIN)
   - Seleccionar usuario
   - Elegir canal: Email, WhatsApp, SMS, Ambos
   - Escribir mensaje
   - ¡Enviar!

3. **Notificaciones en tiempo real** (SSE)
   - Badge con contador
   - Toast de notificación entrante
   - Panel de notificaciones actualizado

---

## 🚀 Próximos pasos recomendados

1. ✅ Instalar librerías: `pip install -r requirements.txt`
2. ✅ Configurar variables de entorno en `.env`
3. ✅ Reiniciar backend
4. ✅ Probar desde el panel de Admin
5. ✅ Guardar números de teléfono en "Preferencias" si quieres WhatsApp/SMS

---

## ⚠️ NOTAS IMPORTANTES

- **Para pruebas sin Twilio**: El sistema usa fallback automático
- **Para pruebas sin SendGrid**: El sistema intenta SMTP Gmail
- **Números de teléfono**: Deben incluir código país (ej: +34 para España, +57 para Colombia)
- **Límites gratis**:
  - Twilio: 100 SMS/mes o crédito de prueba
  - SendGrid: 100 emails/día plan gratis

---

## 📚 Referencias

- Twilio Docs: https://www.twilio.com/docs/sms/quickstart/python
- SendGrid Docs: https://sendgrid.com/docs/for-developers/sending-email/v3-python-mail-send/
- Gmail SMTP: https://support.google.com/accounts/answer/185833
