# Problemas encontrados

## 1. Backend `unhealthy`: "Base de datos no disponible" (puerto 5432 ocupado)

**Categoría:** despliegue / comunicación entre servicios (Docker Compose)

**Síntoma**
- `curl localhost:8000/health/db` devolvía `{"detail":"Base de datos no disponible"}` (503).
- `docker compose ps` mostraba el backend como `unhealthy` y la base de datos sin puertos publicados.

**Diagnóstico**
- Dentro del backend: `psycopg.OperationalError: failed to resolve host 'database'`.
- `docker inspect` mostraba que el contenedor `smartcampus-database` no estaba conectado a ninguna red, mientras que el backend sí estaba en `smartcampus-net`.
- Al recrearlo, Docker dio el error `failed to bind host port 0.0.0.0:5432/tcp: address already in use`: el puerto 5432 de la máquina ya lo usaba otro Postgres local.

**Causa**
Un `docker compose up` anterior dejó el contenedor de la base de datos creado a medias (sin red) porque no pudo publicar el puerto 5432. El backend arrancó, pero no podía resolver el nombre `database`.

**Solución**
Cambiar el puerto publicado en la máquina en el `.env`:

```
DB_PUBLISHED_PORT=5433
```

y recrear los contenedores (sin borrar el volumen):

```
docker compose up -d --force-recreate
```

Solo cambia el puerto visto desde la máquina anfitriona (`localhost:5433`). Entre contenedores se sigue usando `database:5432`.

**Lección:** publicar el puerto de la BD en el host solo es necesario para depurar; si no hace falta, se puede quitar la sección `ports` del servicio `database`.

## 2. El backend no se reinicia tras `docker stop` ni `docker kill` (política `restart`)

**Categoría:** despliegue / resiliencia (Docker Compose)

**Síntoma**
- Con `restart: unless-stopped` en el servicio `backend`, tras `docker kill smartcampus-backend` el contenedor no volvía a arrancar.
- `docker compose ps` no lo mostraba (solo los servicios en ejecución) y `docker compose ps -a` lo daba como `Exited (137)`.

**Diagnóstico**
- `docker inspect smartcampus-backend --format '{{.State.Status}} exit={{.State.ExitCode}} restarts={{.RestartCount}}'` devolvía `exited exit=137 restarts=0`: la política estaba aplicada (`unless-stopped`) pero no se había ejecutado ningún reinicio.
- Docker considera `docker stop` y `docker kill` como una parada manual y, en ese caso, no aplica la política de reinicio. Esta solo actúa cuando el contenedor termina por su cuenta (fallo, error, proceso muerto).
- Intentar simular el fallo desde dentro del contenedor (`os.kill(1, SIGKILL)`) tampoco funciona: el proceso con PID 1 ignora las señales enviadas desde su propio espacio de nombres.

**Solución**
Para simular un fallo real hay que matar el proceso desde el host:

```
sudo kill -9 $(docker inspect -f '{{.State.Pid}}' smartcampus-backend)
docker compose ps
docker inspect smartcampus-backend --format 'restarts={{.RestartCount}}'
```

Resultado: `restarts=1` y el backend vuelve a estar `Up` (primero `health: starting` y después `healthy`). Para recuperar un contenedor parado a mano basta con `docker compose up -d`.

**Lección:** la política `restart` cubre caídas inesperadas, no paradas manuales. Sin ella, ni siquiera un fallo real se recuperaría. En Kubernetes la situación es distinta: un pod borrado a mano sí es recreado porque el ReplicaSet mantiene el estado deseado.

## 3. `minikube image build` falla: "open Dockerfile: no such file or directory"

**Categoría:** construcción de imágenes (Kubernetes)

**Síntoma**
- `minikube -p smartcampus image build -t smartcampus-frontend:1.0 frontend` terminaba con `failed to read dockerfile: open Dockerfile: no such file or directory`, aunque `frontend/Dockerfile` existía. El del backend sí se construía.

**Diagnóstico**
- `frontend/.dockerignore` contenía la línea `Dockerfile`, que excluye el propio Dockerfile del contexto de construcción. `docker build` lo tolera porque lo envía aparte, pero el build de Minikube (BuildKit) no.

**Solución**
Quitar `Dockerfile` de `frontend/.dockerignore` y volver a construir:

```
minikube -p smartcampus image build -t smartcampus-frontend:1.0 frontend
```

**Lección:** no hace falta excluir el Dockerfile en `.dockerignore`, y si se excluye, el mismo build puede funcionar con Docker y fallar con otra herramienta.

## 4. Compose no arranca si ya hay otro proyecto usando el mismo nombre de contenedor y puerto

**Categoría:** despliegue (Docker Compose)

**Síntoma**
- `docker compose up -d --build` daba `The container name "/smartcampus-backend" is already in use` y el backend no se creaba.

**Diagnóstico**
- `docker ps -a` mostraba un contenedor `smartcampus-backend` de otro proyecto (otro directorio de Compose) ya en marcha y publicando el puerto 8000.
- El `docker-compose.yml` fija `container_name`, así que dos proyectos con los mismos nombres no pueden convivir en el mismo Docker.

**Solución**
No tocar el otro proyecto y trabajar el despliegue de Kubernetes en un clúster aparte. Para ejecutar Compose a la vez que el otro habría que parar el otro proyecto o quitar `container_name` y cambiar los puertos publicados.

**Lección:** en Kubernetes este choque no existe: los recursos viven en un namespace propio y los Pods no usan nombres fijos.
