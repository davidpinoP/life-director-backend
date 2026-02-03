# IA Life Director - Backend

Sistema de decisión personal. No acompaña. No motiva. Decide.

## Stack

- Python 3.11+
- FastAPI
- PostgreSQL
- OpenAI GPT-4

## Instalación

```bash
# Clonar repositorio
git clone <repo-url>
cd life-director-backend

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
copy .env.example .env
# Editar .env con tus valores
```

## Base de Datos

```bash
# Iniciar PostgreSQL con Docker
docker-compose up -d db

# O crear base de datos manualmente
createdb life_director
```

## Ejecutar

```bash
# Desarrollo
uvicorn app.main:app --reload

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | /auth/login | Autenticación |
| POST | /auth/register | Registro |
| POST | /onboarding | Envío datos iniciales |
| GET | /onboarding/diagnosis | Obtener diagnóstico |
| POST | /director/daily-plan | Generar plan diario |
| GET | /director/today | Obtener plan de hoy |
| POST | /director/feedback | Enviar feedback |
| GET | /feedback/history | Historial de feedback |
| GET | /feedback/analysis | Análisis de patrones |
| GET | /status | Estado del sistema |
| GET | /health | Health check |

## Tests

```bash
pytest app/tests/ -v
```

## Docker

```bash
# Build y run
docker-compose up --build

# Solo base de datos
docker-compose up -d db
```

## Estructura

```
app/
├── main.py              # Entry point
├── core/                # Configuración y autoridad
├── api/routes/          # Endpoints
├── models/              # Pydantic + SQLAlchemy
├── services/            # Lógica de negocio
├── prompts/             # Prompts para LLM
├── db/                  # Base de datos
├── utils/               # Utilidades
└── tests/               # Tests
```

## Principios

- La IA reduce opciones
- La IA elimina, no añade
- La IA ordena, no aconseja
- Frases cortas
- Sin emojis
- Sin psicología
