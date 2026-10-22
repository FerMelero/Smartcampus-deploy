const API = "/api";

const tablaAulas = document.getElementById("tabla-aulas");
const tablaReservas = document.getElementById("tabla-reservas");
const selectAulas = document.getElementById("select-aulas");
const mensaje = document.getElementById("mensaje");
const estado = document.getElementById("estado");

function mostrarMensaje(texto, ok = false) {
  mensaje.textContent = texto;
  mensaje.className = ok ? "mensaje ok" : "mensaje";
  mensaje.hidden = false;
  setTimeout(() => (mensaje.hidden = true), 4000);
}

async function peticion(ruta, opciones = {}) {
  const res = await fetch(API + ruta, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    const detalle = Array.isArray(error.detail)
      ? error.detail.map((d) => d.msg).join(", ")
      : error.detail;
    throw new Error(detalle || `Error ${res.status}`);
  }
  return res.status === 204 ? null : res.json();
}

async function comprobarEstado() {
  try {
    await peticion("/health/db");
    estado.textContent = "Backend y BD conectados";
    estado.className = "estado ok";
  } catch {
    estado.textContent = "Backend no disponible";
    estado.className = "estado error";
  }
}

function celda(texto) {
  const td = document.createElement("td");
  td.textContent = texto;
  return td;
}

function botonBorrar(onClick) {
  const td = document.createElement("td");
  const boton = document.createElement("button");
  boton.textContent = "Borrar";
  boton.className = "borrar";
  boton.addEventListener("click", onClick);
  td.appendChild(boton);
  return td;
}

async function cargarAulas() {
  const aulas = await peticion("/rooms");
  tablaAulas.replaceChildren();
  selectAulas.replaceChildren();

  for (const aula of aulas) {
    const fila = document.createElement("tr");
    fila.append(
      celda(aula.id),
      celda(aula.nombre),
      celda(aula.edificio),
      celda(aula.capacidad),
      celda(aula.equipamiento.join(", ")),
      botonBorrar(() => borrar(`/rooms/${aula.id}`, "Aula borrada"))
    );
    tablaAulas.appendChild(fila);

    const opcion = document.createElement("option");
    opcion.value = aula.id;
    opcion.textContent = `${aula.id} - ${aula.nombre}`;
    selectAulas.appendChild(opcion);
  }
  return aulas;
}

async function cargarReservas(aulas) {
  const reservas = await peticion("/bookings");
  const nombres = Object.fromEntries(aulas.map((a) => [a.id, a.nombre]));
  tablaReservas.replaceChildren();

  for (const r of reservas) {
    const fila = document.createElement("tr");
    fila.append(
      celda(r.id),
      celda(nombres[r.aula_id] || r.aula_id),
      celda(r.usuario),
      celda(r.fecha),
      celda(r.hora_inicio.slice(0, 5)),
      celda(r.hora_fin.slice(0, 5)),
      botonBorrar(() => borrar(`/bookings/${r.id}`, "Reserva borrada"))
    );
    tablaReservas.appendChild(fila);
  }
}

async function cargarTodo() {
  try {
    const aulas = await cargarAulas();
    await cargarReservas(aulas);
  } catch (e) {
    mostrarMensaje("No se pudieron cargar los datos: " + e.message);
  }
  comprobarEstado();
}

async function borrar(ruta, textoOk) {
  try {
    await peticion(ruta, { method: "DELETE" });
    mostrarMensaje(textoOk, true);
  } catch (e) {
    mostrarMensaje(e.message);
  }
  cargarTodo();
}

document.getElementById("form-aula").addEventListener("submit", async (e) => {
  e.preventDefault();
  const datos = new FormData(e.target);
  const equipamiento = datos
    .get("equipamiento")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  try {
    await peticion("/rooms", {
      method: "POST",
      body: JSON.stringify({
        nombre: datos.get("nombre"),
        edificio: datos.get("edificio"),
        capacidad: Number(datos.get("capacidad")),
        equipamiento,
      }),
    });
    e.target.reset();
    mostrarMensaje("Aula creada", true);
  } catch (err) {
    mostrarMensaje(err.message);
  }
  cargarTodo();
});

document.getElementById("form-reserva").addEventListener("submit", async (e) => {
  e.preventDefault();
  const datos = new FormData(e.target);

  try {
    await peticion("/bookings", {
      method: "POST",
      body: JSON.stringify({
        aula_id: Number(datos.get("aula_id")),
        usuario: datos.get("usuario"),
        fecha: datos.get("fecha"),
        hora_inicio: datos.get("hora_inicio"),
        hora_fin: datos.get("hora_fin"),
      }),
    });
    e.target.reset();
    mostrarMensaje("Reserva creada", true);
  } catch (err) {
    mostrarMensaje(err.message);
  }
  cargarTodo();
});

cargarTodo();
