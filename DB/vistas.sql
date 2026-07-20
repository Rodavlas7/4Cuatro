-- TRACEX — Vistas
-- Version: 2026-07-20


USE cuatro;

-- Eliminar vistas existentes para evitar conflictos
DROP VIEW IF EXISTS vista_lineas;
DROP VIEW IF EXISTS vista_estaciones;
DROP VIEW IF EXISTS vista_ordenes_produccion;


-- VISTA: vista_lineas
--
-- Objetivo : Consulta general del módulo de líneas — une la línea con
--            el nombre de su estado (edo_linea) y el total de estaciones
--            que tiene registradas, para no resolver el join en cada
--            consulta desde el backend.

CREATE VIEW vista_lineas AS
SELECT
    l.codigo,
    l.nombre,
    l.descripcion,
    l.estado           AS estado_codigo,
    el.nombre           AS estado_nombre,
    l.activo,
    COUNT(e.codigo)     AS total_estaciones
FROM linea l
LEFT JOIN edo_linea el ON el.codigo = l.estado
LEFT JOIN estacion  e  ON e.linea   = l.codigo
GROUP BY l.codigo, l.nombre, l.descripcion, l.estado, el.nombre, l.activo;


-- VISTA: vista_estaciones
--
-- Objetivo : Consulta general de estaciones — une la estación con el
--            nombre de su línea y el total de empleados actualmente
--            asignados (empleado_estacion con fecha_fin nula).

CREATE VIEW vista_estaciones AS
SELECT
    e.codigo,
    e.nombre,
    e.descripcion,
    e.linea               AS linea_codigo,
    l.nombre               AS linea_nombre,
    e.activo,
    COUNT(ee.empleado)     AS total_empleados
FROM estacion e
LEFT JOIN linea l ON l.codigo = e.linea
LEFT JOIN empleado_estacion ee
       ON ee.estacion = e.codigo
      AND ee.fecha_fin IS NULL
GROUP BY e.codigo, e.nombre, e.descripcion, e.linea, l.nombre, e.activo;


-- VISTA: vista_ordenes_produccion
--
-- Objetivo : Consulta general del módulo de producción — une la orden con
--            el nombre de su estado (edo_produccion) y el nombre de su
--            modelo de laptop (modelo_laptop). Las cantidades planificada
--            y producida ya vienen guardadas en la propia orden, así que
--            no requieren agregación.

CREATE VIEW vista_ordenes_produccion AS
SELECT
    op.folio,
    op.fecha,
    op.hora,
    op.modelo_laptop   AS modelo_codigo,
    ml.nombre           AS modelo_nombre,
    op.cant_planificada,
    op.cant_producida,
    op.estado           AS estado_codigo,
    ep.nombre            AS estado_nombre
FROM orden_produccion op
LEFT JOIN modelo_laptop ml ON ml.codigo = op.modelo_laptop
LEFT JOIN edo_produccion ep ON ep.codigo = op.estado;
