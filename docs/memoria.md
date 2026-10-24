# Memoria técnica: SmartCampus en Docker y Kubernetes

## 1. Introducción

SmartCampus es una plataforma para gestionar aulas y reservas de espacios universitarios. El objetivo de esta práctica es desplegar la misma aplicación de dos formas, con Docker Compose y con Kubernetes, y comparar ambos enfoques: cómo se construyen las imágenes, cómo se comunican los servicios, qué ocurre cuando algo falla y cómo se escala.

## 2. Arquitectura

La aplicación se divide en tres componentes independientes:

```
Navegador --> frontend (nginx) --/api/--> backend (FastAPI) --SQL--> database (PostgreSQL)
```

| Componente | Tecnología | Función |
|---|---|---|
| frontend | HTML, CSS y JavaScript servidos por nginx | Interfaz web: lista, crea y borra aulas y reservas |
| backend | FastAPI (Python) y psycopg | API REST con la lógica de negocio |
| database | PostgreSQL 16 (imagen oficial) | Almacena aulas y reservas |

**Modelo de datos**
- Aula: `id`, `nombre`, `edificio`, `capacidad`, `equipamiento` (lista).
- Reserva: `id`, `aula_id`, `usuario`, `fecha`, `hora_inicio`, `hora_fin`. Una reserva pertenece a un aula y no puede solaparse con otra del mismo aula y día.

**API del backend**

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Comprueba que el proceso responde (`{"status":"ok"}`) |
| GET | `/health/db` | Comprueba la conexión con la base de datos |
| GET, POST | `/rooms` | Listar y crear aulas |
| GET, DELETE | `/rooms/{id}` | Consultar y borrar un aula |
| GET, POST | `/bookings` | Listar y crear reservas |
| GET, DELETE | `/bookings/{id}` | Consultar y borrar una reserva |

`/health` y `/health/db` están separados a propósito: el primero indica que el proceso está vivo (liveness) y el segundo que además puede hablar con la base de datos (readiness).

**Decisión: el navegador solo habla con nginx.** El frontend llama siempre a rutas relativas (`/api/...`) y nginx las reenvía al backend. Así no hay problemas de CORS y el navegador no necesita resolver el nombre interno del backend, que solo existe dentro de la red de Docker (o del clúster en Kubernetes). La dirección del backend se configura con la variable `BACKEND_URL`, de modo que la misma imagen sirve en Compose (`http://backend:8000`) y, más adelante, en Kubernetes.

## 3. Despliegue con Docker

### 3.1 Imágenes

**Backend** (`backend/Dockerfile`)
- Base `python:3.12-slim`.
- Se copian y se instalan primero los `requirements.txt` y después el código, para aprovechar la caché de capas: si solo cambia el código, las dependencias no se reinstalan.
- Se ejecuta con un usuario sin privilegios (`appuser`).
- La conexión a la base de datos se configura con variables de entorno (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`); la imagen no contiene credenciales.

**Frontend** (`frontend/Dockerfile`)
- Base `nginx:1.27-alpine`.
- Los archivos estáticos se copian a `/usr/share/nginx/html`.
- La configuración de nginx es una plantilla (`nginx.conf.template`) en la que la imagen sustituye `BACKEND_URL` al arrancar.

**Base de datos**
- Se usa la imagen oficial `postgres:16` sin modificar. `database/init.sql` crea las tablas y datos de ejemplo.

### 3.2 Docker Compose

El archivo `docker-compose.yml` define tres servicios en una red propia (`smartcampus-net`):

| Servicio | Puerto en el equipo | Puntos clave |
|---|---|---|
| `database` | 5433 (solo depuración) | Volumen `smartcampus-db-data`, `init.sql` montado en `docker-entrypoint-initdb.d`, healthcheck con `pg_isready` |
| `backend` | 8000 | Variables de entorno desde `.env`, espera a que la base de datos esté `healthy`, healthcheck sobre `/health/db` |
| `frontend` | 8080 | Espera a que el backend esté `healthy`, `BACKEND_URL=http://backend:8000` |

Aspectos de configuración:
- **Service discovery:** los servicios se encuentran por nombre dentro de la red (`database`, `backend`). El backend usa `DB_HOST=database`, no `localhost`.
- **Orden de arranque:** `depends_on` con `condition: service_healthy` evita que el backend arranque antes de que PostgreSQL acepte conexiones.
- **Persistencia:** el volumen nombrado conserva los datos aunque se eliminen los contenedores.
- **Credenciales y puertos:** se leen del archivo `.env` (no versionado); `.env.example` documenta las variables.
- **Resiliencia:** `restart: unless-stopped` en todos los servicios.

`init.sql` solo se ejecuta cuando el volumen de datos está vacío. Si se modifica, hay que recrear el volumen con `docker compose down -v`.

### 3.3 Cómo ejecutarlo

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
```

Web en http://localhost:8080 y API en http://localhost:8000.

## 4. Despliegue en Kubernetes

*Pendiente.*

## 5. Pruebas y evidencias

### 5.1 Docker Compose

**Experimento 1: despliegue y funcionamiento**

![Construcción de las imágenes](capturas/01-compose-build.png)

Construcción de las imágenes con `docker compose up -d --build`.

![docker compose ps](capturas/02-compose-ps.png)

`docker compose ps`: los tres servicios en ejecución; la base de datos y el backend con estado `healthy`.

![Aplicación funcionando](capturas/03-web-funcionando.png)

La web carga las aulas y reservas obtenidas del backend, lo que confirma la cadena frontend → backend → base de datos.

![Pruebas con curl](capturas/04-curl-health-rooms.png)

Comprobación directa de la API: `/health` responde, `/health/db` confirma la conexión con PostgreSQL y `/rooms` devuelve los datos cargados desde `init.sql`.

**Persistencia de datos**

![Creación de un aula](capturas/05-persistencia-crear-aula.png)

Se crea un aula desde la web.

![Datos tras down y up](capturas/06-persistencia-tras-down-up.png)

Tras `docker compose down` (sin `-v`) y `docker compose up -d`, el aula sigue existiendo: los datos viven en el volumen, no en el contenedor.

**Experimento 2: fallo de un contenedor**

![Parada del backend](capturas/07-fallo-parar-backend.png)

Se detiene el backend con `docker stop` / `docker kill`. No se reinicia: Docker lo interpreta como una parada manual y no aplica `restart: unless-stopped`.

![Web con el backend parado](capturas/08-fallo-front-backend-parado.png)

Con el backend parado, el frontend sigue sirviéndose pero indica que el backend no está disponible. La caída de un servicio no tumba a los demás.

![Recuperación manual](capturas/09-fallo-recuperacion-manual.png)

Recuperación manual: `docker compose up -d` vuelve a crear el contenedor que faltaba.

![Reinicio automático](capturas/10-fallo-restart-automatico.png)

Fallo real simulado matando el proceso desde el host (`kill -9`). Docker reinicia el contenedor por su cuenta (`restarts=1`) y pasa de `health: starting` a `healthy`.

Conclusión del experimento: Compose no recupera un contenedor parado a mano, y solo recupera automáticamente los fallos si el servicio tiene una política `restart`. No hay un componente que mantenga un número de réplicas deseado.

### 5.2 Kubernetes

*Pendiente.*

## 6. Comparativa Docker Compose y Kubernetes

*Pendiente.* La columna de Compose, según lo observado:

| Aspecto | Docker Compose |
|---|---|
| Ejecución local | Un solo comando (`docker compose up`), sin instalación adicional |
| Orquestación | Define y arranca un conjunto de contenedores en un único equipo |
| Escalado | `docker compose up --scale servicio=N` en un único equipo; no hay balanceo automático entre réplicas con puertos publicados |
| Self-healing | Solo mediante `restart`; no repone contenedores borrados ni parados a mano |
| Service discovery | DNS interno por nombre de servicio dentro de la red del proyecto |
| Configuración | Variables de entorno y archivo `.env` |
| Secretos | Variables de entorno o archivos; sin gestión específica |
| Alta disponibilidad | No: depende de un único equipo |

## 7. Problemas encontrados

Resumidos aquí y detallados en [problemas.md](problemas.md):

1. Backend `unhealthy` por conflicto del puerto 5432 en el equipo, con el contenedor de la base de datos sin red.
2. El backend no se reiniciaba tras `docker stop`/`docker kill` porque Docker lo trata como parada manual.

## 8. Preguntas

**1. Diferencias entre un contenedor Docker y un Pod.** Un contenedor es una unidad aislada que ejecuta un proceso con su propio sistema de archivos. Un Pod es la unidad mínima de Kubernetes y envuelve uno o varios contenedores que comparten red (una IP y un espacio de puertos) y almacenamiento. Un contenedor se gestiona directamente con Docker; un Pod lo gestiona un controlador (Deployment, StatefulSet) que lo recrea si desaparece.

**2. Qué problema resuelve Docker Compose.** Permite describir en un único archivo una aplicación formada por varios contenedores (imágenes, redes, volúmenes, variables, dependencias, etc) y levantarla o pararla con un comando, en lugar de lanzar y conectar cada contenedor a mano con `docker run`.

**4. Qué ocurre si se borra a mano un contenedor de Compose.** El contenedor desaparece y Compose no lo repone por sí mismo: `restart` no actúa ante una parada o borrado manual. Hay que volver a ejecutar `docker compose up -d`. Se comprobó en el experimento 2.

**13. Cómo se escala con Compose.** Con `docker compose up -d --scale backend=N` se crean N contenedores del servicio. Tiene límites: solo en un equipo, sin balanceo automático si el servicio publica un puerto fijo (las réplicas chocarían) y sin autoescalado.

**18. Cuándo usar Compose.** Para desarrollo local, pruebas, demos y proyectos pequeños de un solo equipo, donde interesa levantar todo rápido y con poca complejidad.

*Pendientes: 3, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 19 y 20.*

## 9. Conclusiones

*Pendiente.*
