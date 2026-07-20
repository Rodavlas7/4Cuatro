-- TRACEX — Vistas
-- Version: 2026-07-20


USE cuatro;

-- Eliminar vistas existentes para evitar conflictos
DROP VIEW IF EXISTS vista_lineas;


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
