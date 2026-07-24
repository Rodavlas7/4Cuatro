-- TRACEX — Vistas
-- Version: 2026-07-20


USE cuatro;

-- Eliminar vistas existentes para evitar conflictos
DROP VIEW IF EXISTS vista_lineas;
DROP VIEW IF EXISTS vista_estaciones;
DROP VIEW IF EXISTS vista_ordenes_produccion;
DROP VIEW IF EXISTS vista_componentes;
DROP VIEW IF EXISTS vista_paros;
DROP VIEW IF EXISTS vista_laptops;
DROP VIEW IF EXISTS vista_empleados;
DROP VIEW IF EXISTS vista_usuarios;
DROP VIEW IF EXISTS vista_inspeccion_calidad;
DROP VIEW IF EXISTS vista_registro_embalaje;



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


-- VISTA: vista_paros
--
-- Objetivo : Consulta general de paros — une el paro con el nombre de
--            su línea y calcula si sigue abierto (fecha_fin nula).

CREATE VIEW vista_paros AS
SELECT
    p.numero,
    p.razon,
    p.fecha_inicio,
    p.hora_inicio,
    p.fecha_fin,
    p.hora_fin,
    p.linea                                          AS linea_codigo,
    l.nombre                                          AS linea_nombre,
    CASE WHEN p.fecha_fin IS NULL THEN 1 ELSE 0 END   AS abierto
FROM paro p
LEFT JOIN linea l ON l.codigo = p.linea;


-- VISTA: vista_laptops
--
-- Objetivo : Consulta general de laptops — une la laptop con los nombres
--            de su modelo (modelo_laptop), su estado (edo_laptop) y su
--            línea (linea), para no resolver esos joins en cada consulta
--            desde el backend.

CREATE VIEW vista_laptops AS
SELECT
    lap.numero,
    lap.num_serie,
    lap.descripcion,
    lap.orden      AS orden_folio,
    lap.modelo     AS modelo_codigo,
    ml.nombre       AS modelo_nombre,
    lap.estado      AS estado_codigo,
    el.nombre        AS estado_nombre,
    lap.linea        AS linea_codigo,
    l.nombre          AS linea_nombre,
    lap.lote          AS lote_codigo
FROM laptop lap
LEFT JOIN modelo_laptop ml ON ml.codigo = lap.modelo
LEFT JOIN edo_laptop    el ON el.codigo = lap.estado
LEFT JOIN linea         l  ON l.codigo  = lap.linea;


-- VISTA: vista_componentes
--
-- Objetivo : Consulta general del módulo de componentes — une el
--            componente con el nombre de su línea, el nombre de su
--            modelo (y fabricante) y el nombre de su estado, para no
--            resolver esos joins en cada consulta desde el backend.

CREATE VIEW vista_componentes AS
SELECT
    c.numero,
    c.num_serie,
    c.descripcion,
    c.linea             AS linea_codigo,
    l.nombre             AS linea_nombre,
    c.orden_material,
    c.registro_ensamblaje,
    c.modelo             AS modelo_codigo,
    mc.nombre            AS modelo_nombre,
    mc.fabricante        AS modelo_fabricante,
    c.lote                AS lote_codigo,
    c.estado              AS estado_codigo,
    ec.nombre              AS estado_nombre
FROM componente c
LEFT JOIN linea             l  ON l.codigo  = c.linea
LEFT JOIN modelo_componente mc ON mc.codigo = c.modelo
LEFT JOIN edo_componente    ec ON ec.codigo = c.estado;






-- VISTA: vista_empleados
--
-- Objetivo : Consulta general del módulo de empleados — une el empleado
--            con su nombre completo, el nombre de su rol y turno, su
--            usuario y el estado (empleado y usuario), para no resolver
--            esos joins en cada consulta desde el backend.

CREATE VIEW vista_empleados AS
SELECT
    e.numero,
    CONCAT(e.nombrePila, ' ', e.primerApell, ' ', IFNULL(e.segundoApell, '')) AS nombre_completo,
    e.rol AS rol_codigo,
    r.nombre AS rol_nombre,
    e.turno AS turno_codigo,
    t.nombre AS turno_nombre,
    u.usuario,
    CASE
        WHEN u.numero IS NULL THEN 'Sin usuario'
        WHEN u.estado = 1 THEN 'Activo'
        ELSE 'Inactivo'
    END AS estado_usuario,
    CASE
        WHEN e.activo = 1 THEN 'Activo'
        ELSE 'Inactivo'
    END AS estado_empleado
FROM empleado e

LEFT JOIN rol r ON r.codigo = e.rol
LEFT JOIN turno t ON t.codigo = e.turno
LEFT JOIN usuario u ON u.empleado = e.numero;



-- VISTA: vista_usuarios
--
-- Objetivo : Consulta general del módulo de usuarios — une la cuenta con
--            el nombre de su empleado, el nombre de su rol y su estado,
--            para no resolver esos joins en cada consulta desde el backend.

CREATE VIEW vista_usuarios AS
SELECT
    u.numero,
    u.usuario,
    e.numero AS empleado_numero,
    CONCAT( e.nombrePila,' ', e.primerApell, ' ', IFNULL(e.segundoApell, '')) AS empleado_nombre,
    r.nombre AS rol_nombre,
    CASE WHEN u.estado = 1 THEN 'Activo'
        ELSE 'Inactivo'
    END AS estado_usuario
FROM usuario u
LEFT JOIN empleado e ON e.numero = u.empleado
LEFT JOIN rol r ON r.codigo = e.rol;

-- VISTA: vista_inspeccion_calidad
--
-- Objetivo : Consulta general del módulo de calidad — une la inspección
--            con el nombre de su resultado, el nombre del empleado que la
--            realizó y el nombre de su línea, para no resolver esos joins
--            en cada consulta desde el backend.

CREATE VIEW vista_inspeccion_calidad AS
SELECT 
    ic.numero,
    ic.resultado,
    CASE 
        WHEN ic.resultado = 1 THEN 'Aprobada'
        WHEN ic.resultado = 0 THEN 'Rechazada'
        WHEN ic.resultado = 2 THEN 'Continuar ensamblaje'
    END AS resultado_nombre,
    ic.observaciones,
    ic.fecha,
    ic.hora,
    ic.laptop AS laptop_numero,
    ic.empleado AS empleado_id,
    CONCAT( e.nombrePila,' ', e.primerApell, ' ', IFNULL(e.segundoApell, '')) AS empleado_nombre,
    ic.linea AS linea_codigo,
    l.nombre AS linea_nombre
FROM inspeccion_calidad ic
LEFT JOIN empleado e ON e.numero = ic.empleado
LEFT JOIN linea l ON l.codigo = ic.linea;




-- VISTA: vista_registro_embalaje
--
-- Objetivo : Consulta general del módulo de embalaje — une el registro
--            con el número de serie de su laptop y el nombre de su tipo
--            de embalaje, para no resolver esos joins en cada consulta
--            desde el backend.

CREATE VIEW vista_registro_embalaje AS
SELECT 
    re.numero,
    re.fecha,
    re.hora,
    re.laptop AS laptop_numero,
    l.num_serie AS laptop_num_serie,
    re.tipo AS tipo_codigo,
    te.nombre AS tipo_nombre
FROM registro_embalaje re
LEFT JOIN tipo_embalaje te ON te.codigo = re.tipo
LEFT JOIN laptop l ON l.numero = re.laptop;