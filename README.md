# SmartCampus Deploy

Práctica 2 de Despliegue y Monitorización en la Nube (UCJC): despliegue de la plataforma SmartCampus (gestión de aulas y reservas) con Docker Compose y Kubernetes.

## Arquitectura

```
Navegador --> frontend (nginx) --/api/--> backend (FastAPI) --SQL--> database (PostgreSQL)
```

- **frontend**: HTML/CSS/JS estático servido por nginx. nginx reenvía `/api/` al backend, así el navegador solo habla con un origen (sin CORS).
- **backend**: API REST con FastAPI y psycopg.
- **database**: PostgreSQL 16 (imagen oficial), con `database/init.sql` para tablas y datos de ejemplo.

## Estructura

```
backend/          API (app/, tests/, Dockerfile)
frontend/         web/ (HTML, CSS, JS), nginx.conf.template, Dockerfile
database/         init.sql
docs/             problemas.md (problemas encontrados y soluciones)
docker-compose.yml
.env.example
```

## Cómo ejecutarlo (Docker Compose)

```bash
cp .env.example .env        # cambiar DB_PASSWORD
docker compose up -d --build
docker compose ps
```

- Web: http://localhost:8080
- API: http://localhost:8000 (documentación en `/docs`)

Parar:

```bash
docker compose down         # conserva los datos de la BD
docker compose down -v      # borra también el volumen
```

Si el puerto 5432 de tu máquina está ocupado, cambia `DB_PUBLISHED_PORT` en `.env` (ver `docs/problemas.md`).

## Endpoints del backend

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Liveness: `{"status":"ok"}` |
| GET | `/health/db` | Comprueba la conexión con la BD |
| GET, POST | `/rooms` | Listar / crear aulas |
| GET, DELETE | `/rooms/{id}` | Ver / borrar un aula |
| GET, POST | `/bookings` | Listar / crear reservas |
| GET, DELETE | `/bookings/{id}` | Ver / borrar una reserva |

## Tests del backend

```bash
cd backend
pip install -r requirements.txt
pytest
```

## Estado del proyecto

### Hecho y probado
- Backend FastAPI con PostgreSQL y todos los endpoints (obligatorios y opcionales).
- `database/init.sql` con tablas y datos de ejemplo.
- Dockerfiles de backend y frontend.
- `docker-compose.yml` con los tres servicios: red propia, volumen para la BD, healthchecks, `depends_on` con `service_healthy` y `restart: unless-stopped`.
- Comunicación frontend → backend → BD funcionando en Compose.

### Pendiente
- Pruebas de Compose con evidencias: persistencia tras `down`/`up` y caída del backend (`docker stop`).
- Manifiestos de Kubernetes (`k8s/`): namespace, ConfigMap, Secret, StatefulSet de la BD, Deployments y Services.
- Pruebas en Minikube: escalado, self-healing y cambio de ConfigMap.
- Memoria técnica: comparativa Compose vs Kubernetes y respuestas a las 20 preguntas.
- Capturas de evidencias.
