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
