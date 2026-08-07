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
DROP VIEW IF EXISTS vista_laptop_linea;
DROP VIEW IF EXISTS vista_empleados;
DROP VIEW IF EXISTS vista_usuarios;
DROP VIEW IF EXISTS vista_inspeccion_calidad;
DROP VIEW IF EXISTS vista_registro_embalaje;

-- Vistas del dashboard de administrador (bloque del final del archivo)
DROP VIEW IF EXISTS vista_dash_produccion_diaria;
DROP VIEW IF EXISTS vista_dash_calidad_diaria;
DROP VIEW IF EXISTS vista_dash_paros_diaria;
DROP VIEW IF EXISTS vista_dash_resumen_planta;
DROP VIEW IF EXISTS vista_dash_stock_componentes;
DROP VIEW IF EXISTS vista_dash_actividad;
DROP VIEW IF EXISTS vista_traza_orden;
DROP VIEW IF EXISTS vista_traza_orden_laptops;
DROP VIEW IF EXISTS vista_traza_orden_componentes;
DROP VIEW IF EXISTS vista_traza_orden_paros;



-- VISTA: vista_lineas
--
-- Objetivo : Consulta general del módulo de líneas — une la línea con
--            el nombre de su estado (edo_linea), el de su tipo (tipo_linea),
--            el de la línea que le sigue en el recorrido y el total de
--            estaciones que tiene registradas, para no resolver el join en
--            cada consulta desde el backend.

CREATE VIEW vista_lineas AS
SELECT
    l.codigo,
    l.nombre,
    l.descripcion,
    l.tipo              AS tipo_codigo,
    tl.nombre           AS tipo_nombre,
    l.estado            AS estado_codigo,
    el.nombre           AS estado_nombre,
    l.siguiente         AS siguiente_codigo,
    sig.nombre          AS siguiente_nombre,
    l.activo,
    COUNT(e.codigo)     AS total_estaciones
FROM linea l
LEFT JOIN edo_linea  el ON el.codigo = l.estado
LEFT JOIN tipo_linea tl ON tl.codigo = l.tipo
LEFT JOIN linea      sig ON sig.codigo = l.siguiente
LEFT JOIN estacion   e  ON e.linea   = l.codigo
GROUP BY l.codigo, l.nombre, l.descripcion, l.tipo, tl.nombre, l.estado, el.nombre,
         l.siguiente, sig.nombre, l.activo;


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
--            el nombre de su estado (edo_produccion), el nombre de su
--            modelo de laptop (modelo_laptop) y su lote (lote_laptop). Las
--            cantidades planificada y producida ya vienen guardadas en la
--            propia orden, así que no requieren agregación.
--
--            El lote se expone aquí porque las laptops lo heredan de su orden
--            al registrarse; el cliente lo necesita para mostrarlo sin pedir
--            el catálogo aparte.

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
    ep.nombre            AS estado_nombre,
    op.lote              AS lote_codigo,
    ll.fecha             AS lote_fecha
FROM orden_produccion op
LEFT JOIN modelo_laptop ml ON ml.codigo = op.modelo_laptop
LEFT JOIN edo_produccion ep ON ep.codigo = op.estado
LEFT JOIN lote_laptop ll ON ll.codigo = op.lote
ORDER BY op.fecha DESC, op.hora DESC;


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
LEFT JOIN linea l ON l.codigo = p.linea
ORDER BY p.fecha_inicio DESC, p.hora_inicio DESC, p.numero DESC;


-- VISTA: vista_laptop_linea
--
-- Objetivo : Decir en qué línea está cada laptop, ahora que la tabla laptop
--            ya no guarda esa columna.
--
--            La línea de una laptop es la de su ensamblaje MÁS RECIENTE: una
--            laptop pasa por varias líneas (linea.siguiente encadena el
--            recorrido) y cada paso deja su propio registro_ensamblaje. El
--            último es dónde está ahora; si nunca se le abrió uno, todavía no
--            está en ninguna línea y las dos columnas salen NULL.
--
--            Va en su propia vista y no repetida en cada consulta porque la
--            usan vista_laptops, el dashboard y trazabilidad. MySQL no deja
--            subconsultas en el FROM de una vista, pero sí unir con otra
--            vista, que es como se enchufa aquí.

CREATE VIEW vista_laptop_linea AS
SELECT
    lap.numero AS laptop,

    (SELECT r.linea
       FROM registro_ensamblaje r
      WHERE r.laptop = lap.numero
      ORDER BY r.fecha_inicio DESC, r.hora_inicio DESC, r.numero DESC
      LIMIT 1)                                                          AS linea_codigo,

    (SELECT li.nombre
       FROM registro_ensamblaje r
       LEFT JOIN linea li ON li.codigo = r.linea
      WHERE r.laptop = lap.numero
      ORDER BY r.fecha_inicio DESC, r.hora_inicio DESC, r.numero DESC
      LIMIT 1)                                                          AS linea_nombre
FROM laptop lap;


-- VISTA: vista_laptops
--
-- Objetivo : Consulta general de laptops — une la laptop con los nombres
--            de su modelo (modelo_laptop) y su estado (edo_laptop), más la
--            línea en la que va (vista_laptop_linea), para no resolver esos
--            joins en cada consulta desde el backend.

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
    vll.linea_codigo AS linea_codigo,
    vll.linea_nombre AS linea_nombre,
    lap.lote          AS lote_codigo
FROM laptop lap
LEFT JOIN modelo_laptop ml ON ml.codigo = lap.modelo
LEFT JOIN edo_laptop    el ON el.codigo = lap.estado
LEFT JOIN vista_laptop_linea vll ON vll.laptop = lap.numero
ORDER BY lap.numero DESC;


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

CREATE OR REPLACE VIEW vista_empleados AS
SELECT
    e.numero,
    CONCAT(
        e.nombrePila, ' ',
        e.primerApell, ' ',
        IFNULL(e.segundoApell, '')
    ) AS nombre_completo,

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
    END AS estado_empleado,

    l.codigo AS linea_codigo,
    l.nombre AS linea_nombre,

    es.codigo AS estacion_codigo,
    es.nombre AS estacion_nombre

FROM empleado e

LEFT JOIN rol r
    ON e.rol = r.codigo

LEFT JOIN turno t
    ON e.turno = t.codigo

LEFT JOIN usuario u
    ON u.empleado = e.numero

LEFT JOIN empleado_linea el
    ON el.empleado = e.numero
   AND el.fecha_fin IS NULL

LEFT JOIN linea l
    ON l.codigo = el.linea

LEFT JOIN empleado_estacion ee
    ON ee.empleado = e.numero
   AND ee.fecha_fin IS NULL

LEFT JOIN estacion es
    ON es.codigo = ee.estacion

ORDER BY e.numero DESC;



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
LEFT JOIN rol r ON r.codigo = e.rol
ORDER BY u.numero DESC;

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
    lp.num_serie AS laptop_num_serie,
    ic.empleado AS empleado_id,
    CONCAT(
        e.nombrePila, ' ',
        e.primerApell, ' ',
        IFNULL(e.segundoApell, '')
    ) AS empleado_nombre,
    ic.linea AS linea_codigo,
    l.nombre AS linea_nombre
FROM inspeccion_calidad ic
LEFT JOIN laptop lp
    ON lp.numero = ic.laptop
LEFT JOIN empleado e
    ON e.numero = ic.empleado
LEFT JOIN linea l
    ON l.codigo = ic.linea

ORDER BY ic.fecha DESC, ic.hora DESC, ic.numero DESC;




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
LEFT JOIN laptop l ON l.numero = re.laptop
ORDER BY re.fecha DESC, re.hora DESC;




-- ============================================================================
--   D A S H B O A R D   D E   A D M I N I S T R A D O R
-- ============================================================================
--
-- Las vistas de aquí abajo son del panel de administrador. Se separan de las de
-- arriba porque son de otra naturaleza: aquéllas resuelven los joins de las
-- pantallas CRUD y devuelven renglones tal cual; éstas ya vienen AGREGADAS
-- (cuentan, suman y agrupan) y nadie escribe a través de ellas.
--
--
-- POR QUÉ AGRUPAN POR DÍA Y NO POR RANGO
-- --------------------------------------
-- En MySQL una vista no recibe parámetros, así que el rango de fechas que el
-- admin elige en pantalla no puede vivir aquí adentro. Y no hace falta: si la
-- vista ya viene agrupada por día, el rango es un simple WHERE de quien la
-- consulta, y un mismo renglón sirve para las dos cosas que pide el dashboard.
--
--     -- las tarjetas suman los días del rango...
--     SELECT SUM(total) FROM vista_dash_produccion_diaria
--      WHERE fecha BETWEEN '2026-07-01' AND '2026-07-31';
--
--     -- ...y las barras usan esos mismos renglones, uno por día
--     SELECT fecha, SUM(total) FROM vista_dash_produccion_diaria
--      WHERE fecha BETWEEN '2026-07-01' AND '2026-07-31'
--      GROUP BY fecha ORDER BY fecha;
--
-- Es el mismo patrón que ya usa ParoListAPIView con fecha_desde/fecha_hasta.
-- Un procedimiento también podría recibir el rango, pero devuelve tuplas sueltas
-- que el ORM no sabe filtrar ni paginar; por eso los procedimientos de este
-- proyecto se quedan para escribir (ver DB/procedimientos.sql) y leer se hace
-- con vistas.
--
--
-- LA COLUMNA `clave`
-- ------------------
-- Django exige una llave primaria para mapear una vista con un modelo
-- managed=False. Las vistas agrupadas no tienen una columna única natural, así
-- que se les arma una pegando las columnas del GROUP BY. No significa nada en
-- el negocio: existe nada más para que el ORM pueda mapear la vista.
--
--
-- QUÉ CUENTA COMO "PRODUCIDA"
-- ---------------------------
-- Una laptop embalada, no una ensamblada. Es el mismo criterio que ya aplica
-- tg_Control_Estado_Orden_Produccion en DB/triggers.sql, donde la orden avanza
-- su cant_producida cuando la laptop llega a EMBALA. La fecha de producción
-- sale de registro_embalaje porque la tabla laptop no guarda ninguna.



-- VISTA: vista_dash_produccion_diaria
--
-- Objetivo : Laptops producidas (embaladas) por día, línea y modelo. Alimenta
--            la tarjeta de producción y la gráfica de barras de tendencia.

CREATE VIEW vista_dash_produccion_diaria AS
SELECT
    CONCAT(re.fecha, '|', IFNULL(vll.linea_codigo, '-'), '|', IFNULL(lap.modelo, '-')) AS clave,
    re.fecha,
    vll.linea_codigo     AS linea_codigo,
    vll.linea_nombre     AS linea_nombre,
    lap.modelo           AS modelo_codigo,
    ml.nombre            AS modelo_nombre,
    COUNT(*)             AS total
FROM registro_embalaje re
JOIN laptop lap            ON lap.numero = re.laptop
LEFT JOIN vista_laptop_linea vll ON vll.laptop = lap.numero
LEFT JOIN modelo_laptop ml ON ml.codigo  = lap.modelo
GROUP BY re.fecha, vll.linea_codigo, vll.linea_nombre, lap.modelo, ml.nombre;


-- VISTA: vista_dash_calidad_diaria
--
-- Objetivo : Inspecciones por día y línea, con los tres resultados ya abiertos
--            en columnas (aprobadas / rechazadas / continuar). Así el % de
--            aprobación es una división y no tres consultas.
--
--            Los códigos de resultado son los mismos de
--            vista_inspeccion_calidad: 1 aprobada, 0 rechazada, 2 continuar.

CREATE VIEW vista_dash_calidad_diaria AS
SELECT
    CONCAT(ic.fecha, '|', IFNULL(ic.linea, '-')) AS clave,
    ic.fecha,
    ic.linea   AS linea_codigo,
    l.nombre   AS linea_nombre,
    COUNT(*)   AS total,
    SUM(CASE WHEN ic.resultado = 1 THEN 1 ELSE 0 END) AS aprobadas,
    SUM(CASE WHEN ic.resultado = 0 THEN 1 ELSE 0 END) AS rechazadas,
    SUM(CASE WHEN ic.resultado = 2 THEN 1 ELSE 0 END) AS continuar
FROM inspeccion_calidad ic
LEFT JOIN linea l ON l.codigo = ic.linea
GROUP BY ic.fecha, ic.linea, l.nombre;


-- VISTA: vista_dash_paros_diaria
--
-- Objetivo : Paros por día de inicio y línea, con cuántos siguen abiertos y
--            cuántos minutos se perdieron. Un paro sin cerrar aporta 0 minutos
--            en lugar de NULL: todavía no se sabe cuánto duró, y sumar NULL
--            envenenaría el total del día.

CREATE VIEW vista_dash_paros_diaria AS
SELECT
    CONCAT(p.fecha_inicio, '|', IFNULL(p.linea, '-')) AS clave,
    p.fecha_inicio AS fecha,
    p.linea    AS linea_codigo,
    l.nombre   AS linea_nombre,
    COUNT(*)   AS total,
    SUM(CASE WHEN p.fecha_fin IS NULL THEN 1 ELSE 0 END) AS abiertos,
    SUM(IFNULL(TIMESTAMPDIFF(
            MINUTE,
            TIMESTAMP(p.fecha_inicio, IFNULL(p.hora_inicio, '00:00:00')),
            TIMESTAMP(p.fecha_fin,    IFNULL(p.hora_fin,    '00:00:00'))
        ), 0)) AS minutos
FROM paro p
LEFT JOIN linea l ON l.codigo = p.linea
GROUP BY p.fecha_inicio, p.linea, l.nombre;


-- VISTA: vista_dash_resumen_planta
--
-- Objetivo : La foto de AHORA MISMO de toda la planta, en un solo renglón.
--            Es lo que no depende de fechas: cuántas líneas están activas,
--            cuántas órdenes siguen abiertas, en qué estado están las laptops
--            y cuánto material hay.
--
--            Va en un renglón y no en varios (métrica, valor) para que el
--            serializer de la API lo devuelva como un objeto plano y la
--            plantilla lo lea con {{ resumen.paros_abiertos }}.

CREATE VIEW vista_dash_resumen_planta AS
SELECT
    1 AS clave,

    -- OJO con las líneas: `estado` y `activo` son dos cosas distintas y hoy no
    -- concuerdan. `estado` dice cómo está operando (ACTI/INAC/PARO/MANT) y
    -- `activo` es la baja lógica que pone el DELETE de la API (lineas/views.py).
    -- El conteo va por `estado`, que es lo que le importa a un dashboard de
    -- planta, y la baja lógica se reporta aparte en lugar de mezclarse.
    --
    -- datos.sql inserta las líneas sin la columna `activo`; hoy es DEFAULT
    -- TRUE, así que nacen dadas de alta y sólo las baja el DELETE de la API.
    (SELECT COUNT(*) FROM linea)                                         AS lineas_totales,
    (SELECT COUNT(*) FROM linea WHERE estado = 'ACTI')                   AS lineas_activas,
    (SELECT COUNT(*) FROM linea WHERE estado = 'INAC')                   AS lineas_inactivas,
    (SELECT COUNT(*) FROM linea WHERE estado = 'PARO')                   AS lineas_en_paro,
    (SELECT COUNT(*) FROM linea WHERE estado = 'MANT')                   AS lineas_en_mantenimiento,
    (SELECT COUNT(*) FROM linea WHERE activo = 0)                        AS lineas_dadas_de_baja,

    (SELECT COUNT(*) FROM orden_produccion WHERE estado = 'PEND')        AS ordenes_pendientes,
    (SELECT COUNT(*) FROM orden_produccion WHERE estado = 'PROC')        AS ordenes_proceso,
    (SELECT COUNT(*) FROM orden_produccion WHERE estado = 'COMP')        AS ordenes_completadas,
    (SELECT COUNT(*) FROM orden_produccion WHERE estado = 'CANC')        AS ordenes_canceladas,

    (SELECT COUNT(*) FROM laptop WHERE estado = 'REGIS')                 AS laptops_registradas,
    (SELECT COUNT(*) FROM laptop WHERE estado = 'PENSAM')                AS laptops_en_ensamblaje,
    (SELECT COUNT(*) FROM laptop WHERE estado = 'APROV')                 AS laptops_aprobadas,
    (SELECT COUNT(*) FROM laptop WHERE estado = 'RECHA')                 AS laptops_rechazadas,
    (SELECT COUNT(*) FROM laptop WHERE estado = 'EMBALA')                AS laptops_embaladas,
    (SELECT COUNT(*) FROM laptop)                                        AS laptops_totales,

    (SELECT COUNT(*) FROM componente WHERE estado = 'EDC001')            AS comp_disponibles,
    (SELECT COUNT(*) FROM componente WHERE estado = 'EDC002')            AS comp_en_uso,
    (SELECT COUNT(*) FROM componente WHERE estado = 'EDC003')            AS comp_danados,
    (SELECT COUNT(*) FROM componente WHERE estado = 'EDC004')            AS comp_mermados,

    (SELECT COUNT(*) FROM paro WHERE fecha_fin IS NULL)                  AS paros_abiertos,

    (SELECT COUNT(*) FROM empleado WHERE activo = 1)                     AS empleados_activos,
    (SELECT COUNT(*) FROM usuario  WHERE estado = 1)                     AS usuarios_activos;


-- VISTA: vista_dash_stock_componentes
--
-- Objetivo : Inventario por modelo de componente, con las piezas repartidas
--            entre los cuatro estados. Alimenta la alerta de material bajo:
--            el umbral NO se pone aquí (es una decisión de pantalla, no de
--            base), la API filtra con disponibles <= N.
--
--            Arranca en modelo_componente y no en componente para que un
--            modelo sin ninguna pieza salga con 0 en lugar de desaparecer:
--            justo ése es el que hay que comprar.

CREATE VIEW vista_dash_stock_componentes AS
SELECT
    mc.codigo      AS modelo_codigo,
    mc.nombre      AS modelo_nombre,
    mc.fabricante,
    mc.tipo_componente AS tipo_codigo,
    tc.nombre      AS tipo_nombre,
    COUNT(c.numero) AS total,
    SUM(CASE WHEN c.estado = 'EDC001' THEN 1 ELSE 0 END) AS disponibles,
    SUM(CASE WHEN c.estado = 'EDC002' THEN 1 ELSE 0 END) AS en_uso,
    SUM(CASE WHEN c.estado = 'EDC003' THEN 1 ELSE 0 END) AS danados,
    SUM(CASE WHEN c.estado = 'EDC004' THEN 1 ELSE 0 END) AS mermados
FROM modelo_componente mc
LEFT JOIN componente c  ON c.modelo  = mc.codigo
LEFT JOIN tipo_comp  tc ON tc.codigo = mc.tipo_componente
GROUP BY mc.codigo, mc.nombre, mc.fabricante, mc.tipo_componente, tc.nombre;


-- VISTA: vista_dash_actividad
--
-- Objetivo : Línea de tiempo de lo último que pasó en el sistema. El proyecto
--            no tiene tabla de bitácora, así que se arma juntando las cinco
--            tablas que sí guardan fecha y hora.
--
--            Los CAST(NULL AS ...) no son adorno: en un UNION, MySQL decide el
--            tipo de cada columna mezclando todas las ramas, y una rama que
--            aporta NULL pelón puede dejar la columna más corta de lo que
--            necesitan las demás. Con el CAST el tipo queda dicho a la fuerza.
--
--            Y el COLLATE que los acompaña tampoco: las columnas de las tablas
--            son utf8mb4_unicode_ci (así crea la base estructura.sql), pero un
--            literal o un CAST nacen con la colación de la CONEXIÓN, que suele
--            ser utf8mb4_0900_ai_ci. Mezclar las dos en un UNION revienta con
--            "Illegal mix of collations", y la vista queda sin crearse. Decirlo
--            aquí hace que el archivo corra igual desde cualquier cliente.
--
--            Quien la consulta ordena por fecha y hora y corta con LIMIT.

CREATE VIEW vista_dash_actividad AS

    SELECT
        CONCAT('EMB-', re.numero)          AS clave,
        'EMBALAJE'                         AS tipo,
        'Laptop embalada'                  AS titulo,
        re.fecha,
        re.hora,
        CONCAT('Serie ', IFNULL(lap.num_serie, '?'),
               ' · ', IFNULL(te.nombre, 'sin tipo'))            AS detalle,
        re.laptop                          AS referencia,
        vll.linea_codigo                   AS linea_codigo,
        vll.linea_nombre                   AS linea_nombre
    FROM registro_embalaje re
    LEFT JOIN laptop lap        ON lap.numero = re.laptop
    LEFT JOIN tipo_embalaje te  ON te.codigo  = re.tipo
    LEFT JOIN vista_laptop_linea vll ON vll.laptop = lap.numero

UNION ALL

    SELECT
        CONCAT('INS-', ic.numero),
        'CALIDAD',
        CASE ic.resultado
            WHEN 1 THEN 'Inspección aprobada'
            WHEN 0 THEN 'Inspección rechazada'
            WHEN 2 THEN 'Inspección: continuar ensamblaje'
            ELSE        'Inspección registrada'
        END,
        ic.fecha,
        ic.hora,
        CONCAT('Serie ', IFNULL(lap.num_serie, '?'),
               ' · ', IFNULL(CONCAT(e.nombrePila, ' ', e.primerApell), 'sin inspector')),
        ic.laptop,
        ic.linea,
        l.nombre
    FROM inspeccion_calidad ic
    LEFT JOIN laptop   lap ON lap.numero = ic.laptop
    LEFT JOIN empleado e   ON e.numero   = ic.empleado
    LEFT JOIN linea    l   ON l.codigo   = ic.linea

UNION ALL

    SELECT
        CONCAT('ENS-', r.numero),
        'ENSAMBLAJE',
        CASE WHEN r.fecha_fin IS NULL THEN 'Ensamblaje iniciado'
             ELSE                          'Ensamblaje terminado' END,
        IFNULL(r.fecha_fin, r.fecha_inicio),
        IFNULL(r.hora_fin,  r.hora_inicio),
        CONCAT('Serie ', IFNULL(lap.num_serie, '?'),
               ' · ', (SELECT COUNT(*) FROM componente c
                        WHERE c.registro_ensamblaje = r.numero), ' componentes'),
        r.laptop,
        r.linea,
        l.nombre
    FROM registro_ensamblaje r
    LEFT JOIN laptop lap ON lap.numero = r.laptop
    LEFT JOIN linea  l   ON l.codigo   = r.linea

UNION ALL

    SELECT
        CONCAT('PAR-', p.numero),
        'PARO',
        CASE WHEN p.fecha_fin IS NULL THEN 'Paro de línea abierto'
             ELSE                          'Paro de línea cerrado' END,
        IFNULL(p.fecha_fin, p.fecha_inicio),
        IFNULL(p.hora_fin,  p.hora_inicio),
        IFNULL(p.razon, 'sin razón registrada'),
        p.numero,
        p.linea,
        l.nombre
    FROM paro p
    LEFT JOIN linea l ON l.codigo = p.linea

UNION ALL

    SELECT
        CONCAT('ORD-', op.folio),
        'ORDEN',
        'Orden de producción creada',
        op.fecha,
        op.hora,
        CONCAT('Folio ', op.folio,
               ' · ', IFNULL(ml.nombre, 'sin modelo'),
               ' · ', IFNULL(op.cant_planificada, 0), ' pzas'),
        op.folio,
        CAST(NULL AS CHAR(8))  COLLATE utf8mb4_unicode_ci,
        CAST(NULL AS CHAR(32)) COLLATE utf8mb4_unicode_ci
    FROM orden_produccion op
    LEFT JOIN modelo_laptop ml ON ml.codigo = op.modelo_laptop;



-- ============================================================================
--   T R A Z A B I L I D A D   P O R   O R D E N   D E   P R O D U C C I Ó N
-- ============================================================================
--
-- Las cuatro vistas de abajo contestan la misma pregunta desde cuatro ángulos:
-- "cuéntame todo lo que le pasó al folio N". Se filtran siempre por
-- orden_folio, y juntas arman la pantalla de trazabilidad.
--
-- El hilo que las une es siempre el mismo camino:
--
--     orden_produccion → laptop → registro_ensamblaje → componente
--
-- Están separadas en lugar de ser una sola vista gigante porque cada una tiene
-- su propia granularidad (una orden, una laptop, un modelo de componente, un
-- paro) y mezclarlas obligaría a multiplicar renglones.


-- VISTA: vista_traza_orden
--
-- Objetivo : El encabezado de la trazabilidad — la orden con su avance y el
--            conteo de sus laptops por estado, sus inspecciones y su material.
--
--            Repite las columnas de vista_ordenes_produccion a propósito: así
--            la pantalla de trazabilidad se sirve de una sola consulta y no
--            depende de la vista del CRUD, que es de otro equipo.

CREATE VIEW vista_traza_orden AS
SELECT
    op.folio,
    op.fecha,
    op.hora,
    op.modelo_laptop  AS modelo_codigo,
    ml.nombre         AS modelo_nombre,
    op.cant_planificada,
    op.cant_producida,
    op.estado         AS estado_codigo,
    ep.nombre         AS estado_nombre,
    op.lote           AS lote_codigo,
    ll.fecha          AS lote_fecha,

    -- Avance en porcentaje. NULLIF evita la división entre cero cuando la
    -- orden se guardó sin cantidad planificada.
    IFNULL(ROUND(100 * op.cant_producida / NULLIF(op.cant_planificada, 0)), 0) AS avance,

    (SELECT COUNT(*) FROM laptop x WHERE x.orden = op.folio)                          AS laptops_totales,
    (SELECT COUNT(*) FROM laptop x WHERE x.orden = op.folio AND x.estado = 'REGIS')   AS laptops_registradas,
    (SELECT COUNT(*) FROM laptop x WHERE x.orden = op.folio AND x.estado = 'PENSAM')  AS laptops_en_ensamblaje,
    (SELECT COUNT(*) FROM laptop x WHERE x.orden = op.folio AND x.estado = 'APROV')   AS laptops_aprobadas,
    (SELECT COUNT(*) FROM laptop x WHERE x.orden = op.folio AND x.estado = 'RECHA')   AS laptops_rechazadas,
    (SELECT COUNT(*) FROM laptop x WHERE x.orden = op.folio AND x.estado = 'EMBALA')  AS laptops_embaladas,

    (SELECT COUNT(*)
       FROM inspeccion_calidad ic
       JOIN laptop x ON x.numero = ic.laptop
      WHERE x.orden = op.folio)                                   AS inspecciones,
    (SELECT COUNT(*)
       FROM inspeccion_calidad ic
       JOIN laptop x ON x.numero = ic.laptop
      WHERE x.orden = op.folio AND ic.resultado = 0)              AS inspecciones_rechazadas,

    (SELECT COUNT(*)
       FROM componente c
       JOIN registro_ensamblaje r ON r.numero = c.registro_ensamblaje
       JOIN laptop x              ON x.numero = r.laptop
      WHERE x.orden = op.folio)                                   AS componentes_usados,

    (SELECT MIN(r.fecha_inicio)
       FROM registro_ensamblaje r
       JOIN laptop x ON x.numero = r.laptop
      WHERE x.orden = op.folio)                                   AS ensamblaje_inicio,
    (SELECT MAX(r.fecha_fin)
       FROM registro_ensamblaje r
       JOIN laptop x ON x.numero = r.laptop
      WHERE x.orden = op.folio)                                   AS ensamblaje_fin

FROM orden_produccion op
LEFT JOIN modelo_laptop  ml ON ml.codigo = op.modelo_laptop
LEFT JOIN edo_produccion ep ON ep.codigo = op.estado
LEFT JOIN lote_laptop    ll ON ll.codigo = op.lote;


-- VISTA: vista_traza_orden_laptops
--
-- Objetivo : Las laptops de la orden, una por renglón, con su paso por
--            ensamblaje, calidad y embalaje.
--
--            El ensamblaje y el embalaje entran por subconsulta y no por JOIN
--            aposta: una laptop puede tener más de un registro_ensamblaje, y
--            un JOIN la duplicaría en la tabla de pantalla. Con MIN/MAX el
--            renglón sigue siendo uno por laptop, que es como se lee.

CREATE VIEW vista_traza_orden_laptops AS
SELECT
    lap.numero,
    lap.num_serie,
    lap.orden      AS orden_folio,
    lap.modelo     AS modelo_codigo,
    ml.nombre      AS modelo_nombre,
    lap.estado     AS estado_codigo,
    el.nombre      AS estado_nombre,
    vll.linea_codigo AS linea_codigo,
    vll.linea_nombre AS linea_nombre,
    lap.lote       AS lote_codigo,

    (SELECT COUNT(*)        FROM registro_ensamblaje r WHERE r.laptop = lap.numero) AS ensamblajes,
    (SELECT MIN(r.fecha_inicio) FROM registro_ensamblaje r WHERE r.laptop = lap.numero) AS ensamblaje_inicio,
    (SELECT MAX(r.fecha_fin)    FROM registro_ensamblaje r WHERE r.laptop = lap.numero) AS ensamblaje_fin,

    (SELECT COUNT(*)
       FROM componente c
       JOIN registro_ensamblaje r ON r.numero = c.registro_ensamblaje
      WHERE r.laptop = lap.numero)                                     AS componentes,

    (SELECT COUNT(*) FROM inspeccion_calidad ic WHERE ic.laptop = lap.numero) AS inspecciones,

    -- Resultado de la última inspección: 1 aprobada, 0 rechazada, 2 continuar,
    -- NULL si nunca pasó por calidad.
    (SELECT ic.resultado
       FROM inspeccion_calidad ic
      WHERE ic.laptop = lap.numero
      ORDER BY ic.fecha DESC, ic.hora DESC, ic.numero DESC
      LIMIT 1)                                                          AS ultimo_resultado,

    (SELECT MAX(e.fecha) FROM registro_embalaje e WHERE e.laptop = lap.numero) AS embalaje_fecha

FROM laptop lap
LEFT JOIN modelo_laptop ml ON ml.codigo = lap.modelo
LEFT JOIN edo_laptop    el ON el.codigo = lap.estado
LEFT JOIN vista_laptop_linea vll ON vll.laptop = lap.numero;


-- VISTA: vista_traza_orden_componentes
--
-- Objetivo : Qué material se consumió en la orden, agrupado por modelo de
--            componente y lote. Con esto el admin ve de qué lote y de qué
--            fabricante salieron las piezas de una orden.
--
--            Los JOIN son cerrados (no LEFT) a propósito: sólo cuentan los
--            componentes que de verdad quedaron montados en una laptop de la
--            orden, no los que nada más están en inventario.

CREATE VIEW vista_traza_orden_componentes AS
SELECT
    CONCAT(x.orden, '|', IFNULL(c.modelo, '-'), '|', IFNULL(c.lote, '-')) AS clave,
    x.orden         AS orden_folio,
    c.modelo        AS modelo_codigo,
    mc.nombre       AS modelo_nombre,
    mc.fabricante,
    tc.nombre       AS tipo_nombre,
    c.lote          AS lote_codigo,
    COUNT(*)                  AS piezas,
    COUNT(DISTINCT x.numero)  AS laptops,
    SUM(CASE WHEN c.estado = 'EDC004' THEN 1 ELSE 0 END) AS mermados
FROM componente c
JOIN registro_ensamblaje r  ON r.numero = c.registro_ensamblaje
JOIN laptop x               ON x.numero = r.laptop
LEFT JOIN modelo_componente mc ON mc.codigo = c.modelo
LEFT JOIN tipo_comp         tc ON tc.codigo = mc.tipo_componente
GROUP BY x.orden, c.modelo, mc.nombre, mc.fabricante, tc.nombre, c.lote;


-- VISTA: vista_traza_orden_paros
--
-- Objetivo : Los paros que le pegaron a la orden. No hay relación directa
--            entre paro y orden en la base, así que se cruzan por el único
--            terreno que comparten: la línea y el tiempo.
--
--            Un paro entra si ocurrió en una línea por donde pasaron laptops
--            de la orden Y empezó el día que se creó la orden o después. Es
--            una aproximación, no un vínculo formal, y por eso se llama
--            "paros de sus líneas" en pantalla y no "paros de la orden".
--
--            El puente es registro_ensamblaje y no la laptop: la laptop ya no
--            guarda línea. Se toman TODOS sus ensamblajes, no nada más el
--            último, porque un paro en cualquier línea del recorrido le pegó
--            a la orden igual. El DISTINCT es el que evita que un paro salga
--            repetido por cada laptop que pasó por esa línea.

CREATE VIEW vista_traza_orden_paros AS
SELECT DISTINCT
    CONCAT(x.orden, '|', p.numero) AS clave,
    x.orden        AS orden_folio,
    p.numero,
    p.razon,
    p.fecha_inicio,
    p.hora_inicio,
    p.fecha_fin,
    p.hora_fin,
    p.linea        AS linea_codigo,
    l.nombre       AS linea_nombre,
    CASE WHEN p.fecha_fin IS NULL THEN 1 ELSE 0 END AS abierto,
    IFNULL(TIMESTAMPDIFF(
        MINUTE,
        TIMESTAMP(p.fecha_inicio, IFNULL(p.hora_inicio, '00:00:00')),
        TIMESTAMP(p.fecha_fin,    IFNULL(p.hora_fin,    '00:00:00'))
    ), 0) AS minutos
FROM paro p
JOIN registro_ensamblaje r ON r.linea  = p.linea
JOIN laptop x              ON x.numero = r.laptop
JOIN orden_produccion o    ON o.folio  = x.orden
LEFT JOIN linea l          ON l.codigo = p.linea
WHERE p.fecha_inicio >= o.fecha;