# Deploy en Render — ControlPro V11

Crear un **Web Service** conectado al repo.

Build Command:

```text
pip install -r requirements.txt
```

Start Command:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Variables de entorno recomendadas en Render:

```text
APP_ENV=pilot
CONTROLPRO_REQUIRE_HUMAN_APPROVAL=true
CONTROLPRO_RFQ_CONFIRMATION_REQUIRED=true
```

Para activar integraciones, copiar valores desde `.env.example` al panel de Environment de Render.

No activar WhatsApp/SMTP sin consentimiento y prueba controlada.
