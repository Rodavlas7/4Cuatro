-- TRACEX — Procedimientos almacenados
-- Version: 2026-07-31
--
-- Qué hay aquí
-- ------------
-- Operaciones que tocan muchas filas de varias tablas y tienen que pasar o no
-- pasar completas. En Python serían un bucle de N viajes a la base sin
-- atomicidad real; aquí son una sola llamada y una sola transacción.
--
-- NO son reglas de negocio sueltas: esas viven en DB/triggers.sql. Estos tres
-- son acciones que alguien dispara a propósito desde una pantalla.
--
-- Cómo se cargan (después de estructura.sql, vistas.sql y triggers.sql):
--
--     mysql -u root cuatro < DB/procedimientos.sql
--
-- Es idempotente por los DROP de abajo: córrelo las veces que quieras.
--
-- Convención de errores
-- ---------------------
-- Igual que los triggers: SIGNAL SQLSTATE '45000' con el texto en español y el
-- prefijo 'Error sp_Nombre:'. La API ya sabe traducir eso a un 400 legible
-- (ver api/errores.py, mensaje_de_base), así que el motivo llega a pantalla
-- sin escribir nada extra.
--
-- Cada procedimiento termina con un SELECT de resumen. Se usa SELECT y no
-- parámetros OUT porque mysqlclient deja los OUT en variables de sesión
-- (@_sp_nombre_0) que luego hay que ir a consultar aparte; un SELECT final se
-- lee directo con cursor.fetchall().


USE cuatro;

DROP PROCEDURE IF EXISTS sp_Liberar_Componentes_Laptop;
DROP PROCEDURE IF EXISTS sp_Cancelar_Orden_Produccion;
DROP PROCEDURE IF EXISTS sp_Iniciar_Ensamblaje_Orden;
DROP PROCEDURE IF EXISTS sp_Dashboard_Resumen;

DELIMITER $$


-- ============================================================
-- 1. sp_Liberar_Componentes_Laptop
-- ============================================================
--
-- Objetivo : Desarmar una laptop. Suelta todos los componentes que tiene
--            montados, los devuelve al inventario y cierra su ensamblaje.
--
-- Parámetros:
--   p_laptop          Número de la laptop a desarmar.
--   p_estado_destino  A qué estado regresan los componentes:
--                       EDC001 (Disponible) si sirven y vuelven al inventario
--                       EDC003 (Dañado)     si salieron defectuosos
--                     NULL se toma como EDC001.
--
-- Qué NO toca:
--   - Los componentes Mermados (EDC004). Están perdidos, no regresan al
--     inventario, y se les deja su vínculo con el ensamblaje para que el
--     historial siga diciendo en qué laptop se perdieron.
--   - El estado de la laptop. Quien llama decide qué hacer con ella
--     (sp_Cancelar_Orden_Produccion, por ejemplo, la pasa a Rechazada).
--
-- OJO: al cerrar el ensamblaje (fecha_fin), tg_Control_Componentes_Duplicados
--   impide abrirle uno nuevo a esa laptop. O sea que desarmarla es definitivo:
--   ya no se vuelve a armar. Es a propósito, para no perder el historial.

CREATE PROCEDURE sp_Liberar_Componentes_Laptop(
    IN p_laptop         INT,
    IN p_estado_destino VARCHAR(8)
)
BEGIN
    DECLARE destino_componentes VARCHAR(8);
    DECLARE laptop_existe       INT;
    DECLARE total_liberados     INT DEFAULT 0;
    DECLARE total_mermados      INT DEFAULT 0;
    DECLARE total_cerrados      INT DEFAULT 0;

    SET destino_componentes = IFNULL(p_estado_destino, 'EDC001');

    -- Validaciones

    SELECT COUNT(*) INTO laptop_existe FROM laptop WHERE numero = p_laptop;

    IF laptop_existe = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Liberar_Componentes_Laptop: esa laptop no existe';
    END IF;

    IF destino_componentes NOT IN ('EDC001', 'EDC003') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Liberar_Componentes_Laptop: los componentes solo pueden regresar a Disponible o Dañado';
    END IF;

    -- Cuántos se van a quedar como están, para reportarlo
    SELECT COUNT(*)
      INTO total_mermados
      FROM componente c
      JOIN registro_ensamblaje re ON re.numero = c.registro_ensamblaje
     WHERE re.laptop = p_laptop
       AND c.estado  = 'EDC004';

    -- Soltar los componentes montados.
    -- El estado admite nulos, así que se compara con IS NULL OR <>: un
    -- 'NULL <> EDC004' no es TRUE, es NULL, y esas filas se quedarían fuera.
    UPDATE componente c
      JOIN registro_ensamblaje re ON re.numero = c.registro_ensamblaje
       SET c.estado              = destino_componentes,
           c.registro_ensamblaje = NULL
     WHERE re.laptop = p_laptop
       AND (c.estado IS NULL OR c.estado <> 'EDC004');

    SET total_liberados = ROW_COUNT();

    -- Cerrar los ensamblajes que siguieran abiertos
    UPDATE registro_ensamblaje
       SET fecha_fin = CURDATE(),
           hora_fin  = CURTIME()
     WHERE laptop    = p_laptop
       AND fecha_fin IS NULL;

    SET total_cerrados = ROW_COUNT();

    SELECT p_laptop            AS laptop,
           total_liberados     AS componentes_liberados,
           destino_componentes AS estado_destino,
           total_mermados      AS mermados_conservados,
           total_cerrados      AS ensamblajes_cerrados;
END$$



-- ============================================================
-- 2. sp_Cancelar_Orden_Produccion
-- ============================================================
--
-- Objetivo : Cancelar una orden y dejar la planta consistente: el material que
--            tenía apartado vuelve al inventario y las laptops a medias se dan
--            por perdidas.
--
-- Parámetros:
--   p_folio  Folio de la orden a cancelar.
--
-- Qué hace, en orden:
--   1. Suelta los componentes de las laptops NO terminadas de esa orden
--      (Registrada / En Ensamblaje) y cierra sus ensamblajes.
--   2. Pasa esas laptops a Rechazada.
--   3. Pasa la orden a Cancelada.
--
-- Qué NO toca:
--   - Las laptops Aprobadas y Embaladas. Ya pasaron calidad y existen
--     físicamente: cancelar la orden no es razón para tirarlas.
--   - cant_producida. La recalculan solos los triggers
--     tg_Sincronizar_Cant_Producida_* al cambiar el estado de las laptops.
--
-- Se repiten aquí los dos UPDATE de sp_Liberar_Componentes_Laptop en vez de
-- llamarlo en un bucle, por dos razones: así es un UPDATE por toda la orden en
-- lugar de N llamadas, y porque el SELECT de resumen de aquel se le devolvería
-- al cliente una vez por laptop. Si cambias la lógica de liberación, cámbiala
-- en los dos lados.
--
-- NOTA: la orden no tiene columna para el motivo de la cancelación, así que no
--   se guarda. Si lo necesitan, hay que agregarle una a orden_produccion.

CREATE PROCEDURE sp_Cancelar_Orden_Produccion(
    IN p_folio INT
)
BEGIN
    DECLARE estado_orden      VARCHAR(8);
    DECLARE total_liberados   INT DEFAULT 0;
    DECLARE total_rechazadas  INT DEFAULT 0;
    DECLARE total_respetadas  INT DEFAULT 0;

    -- Validaciones

    SELECT estado INTO estado_orden
      FROM orden_produccion
     WHERE folio = p_folio;

    IF estado_orden IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Cancelar_Orden_Produccion: esa orden no existe o no tiene estado';
    END IF;

    IF estado_orden = 'CANC' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Cancelar_Orden_Produccion: esa orden ya estaba cancelada';
    END IF;

    IF estado_orden = 'COMP' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Cancelar_Orden_Produccion: esa orden ya se completó, no se puede cancelar';
    END IF;

    -- Cuántas laptops terminadas se van a respetar, para reportarlo
    SELECT COUNT(*)
      INTO total_respetadas
      FROM laptop
     WHERE orden  = p_folio
       AND estado IN ('APROV', 'EMBALA');

    -- 1. Soltar los componentes de las laptops no terminadas
    UPDATE componente c
      JOIN registro_ensamblaje re ON re.numero = c.registro_ensamblaje
      JOIN laptop             l  ON l.numero  = re.laptop
       SET c.estado              = 'EDC001',
           c.registro_ensamblaje = NULL
     WHERE l.orden  = p_folio
       AND l.estado IN ('REGIS', 'PENSAM')
       AND (c.estado IS NULL OR c.estado <> 'EDC004');

    SET total_liberados = ROW_COUNT();

    UPDATE registro_ensamblaje re
      JOIN laptop l ON l.numero = re.laptop
       SET re.fecha_fin = CURDATE(),
           re.hora_fin  = CURTIME()
     WHERE l.orden       = p_folio
       AND l.estado      IN ('REGIS', 'PENSAM')
       AND re.fecha_fin  IS NULL;

    -- 2. Las laptops a medias se dan por perdidas
    UPDATE laptop
       SET estado = 'RECHA'
     WHERE orden  = p_folio
       AND estado IN ('REGIS', 'PENSAM');

    SET total_rechazadas = ROW_COUNT();

    -- 3. La orden queda cancelada
    UPDATE orden_produccion
       SET estado = 'CANC'
     WHERE folio  = p_folio;

    SELECT p_folio          AS folio,
           total_rechazadas AS laptops_rechazadas,
           total_respetadas AS laptops_respetadas,
           total_liberados  AS componentes_liberados;
END$$



-- ============================================================
-- 3. sp_Iniciar_Ensamblaje_Orden
-- ============================================================
--
-- Objetivo : Dar de alta de un jalón las laptops que le faltan a una orden
--            para llegar a su cantidad planificada.
--
-- Parámetros:
--   p_folio  Folio de la orden.
--
-- Qué hace:
--   Crea (cant_planificada - las que ya existen) laptops en estado Registrada,
--   heredando el modelo y el lote de la orden. NO abre el registro de
--   ensamblaje: eso sigue siendo laptop por laptop, cuando de verdad arranca.
--
--   La línea ya NO se pide. La tabla laptop no tiene columna de línea: dónde
--   se está armando una laptop lo dice su registro_ensamblaje, y ése se abre
--   después, unidad por unidad. Estas laptops nacen sin línea, que es lo
--   correcto: todavía no las está armando nadie.
--
-- Se puede correr dos veces sin duplicar: siempre mira cuántas faltan.
--
-- El número de serie sale provisional (TMP-0001, TMP-0002...), que es la
-- convención que ya usa el cliente. La columna es NOT NULL, así que no puede
-- quedar vacía.
--
-- OJO: hoy la serie definitiva NO se llega a asignar. El trigger
--   tg_Generar_Numero_Serie_Final solo actúa si num_serie viene vacío o nulo al
--   aprobar la laptop, y 'TMP-0001' no lo está. Le pasa igual a las laptops que
--   se dan de alta desde el cliente, así que no es algo que introduzca este
--   procedimiento, pero hay que arreglarlo en el trigger.
--
-- Los triggers que se disparan solos al insertar:
--   tg_Iniciar_Orden_Al_Registrar_Laptop  → si la orden estaba Pendiente,
--                                            pasa a En Proceso.
--   tg_Sincronizar_Cant_Producida_Alta    → recuenta cant_producida. Como las
--                                            nuevas nacen Registradas y ese
--                                            conteo solo suma Aprobadas y
--                                            Embaladas, no la infla.

CREATE PROCEDURE sp_Iniciar_Ensamblaje_Orden(
    IN p_folio INT
)
BEGIN
    DECLARE estado_orden       VARCHAR(8);
    DECLARE modelo_orden       VARCHAR(8);
    DECLARE lote_orden         VARCHAR(8);
    DECLARE total_planificadas INT;
    DECLARE total_existentes   INT;
    DECLARE total_faltantes    INT;
    DECLARE consecutivo_serie  INT;
    DECLARE total_creadas      INT DEFAULT 0;

    -- Validaciones

    SELECT estado, modelo_laptop, lote, IFNULL(cant_planificada, 0)
      INTO estado_orden, modelo_orden, lote_orden, total_planificadas
      FROM orden_produccion
     WHERE folio = p_folio;

    IF estado_orden IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Iniciar_Ensamblaje_Orden: esa orden no existe o no tiene estado';
    END IF;

    IF estado_orden NOT IN ('PEND', 'PROC') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Iniciar_Ensamblaje_Orden: solo se le pueden agregar laptops a una orden Pendiente o En Proceso';
    END IF;

    IF modelo_orden IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Iniciar_Ensamblaje_Orden: la orden no tiene modelo de laptop, no se sabe qué fabricar';
    END IF;

    -- Cuántas faltan

    SELECT COUNT(*) INTO total_existentes FROM laptop WHERE orden = p_folio;

    SET total_faltantes = total_planificadas - total_existentes;

    IF total_faltantes <= 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Iniciar_Ensamblaje_Orden: esta orden ya tiene todas las laptops que planificó';
    END IF;

    -- Desde qué consecutivo seguir con las series provisionales
    SELECT IFNULL(MAX(CAST(SUBSTRING(num_serie, 5) AS UNSIGNED)), 0)
      INTO consecutivo_serie
      FROM laptop
     WHERE num_serie LIKE 'TMP-%';

    WHILE total_creadas < total_faltantes DO

        SET consecutivo_serie = consecutivo_serie + 1;

        INSERT INTO laptop (num_serie, descripcion, orden, modelo, estado, lote)
        VALUES (CONCAT('TMP-', LPAD(consecutivo_serie, 4, '0')),
                CONCAT('Alta en lote de la orden #', p_folio),
                p_folio,
                modelo_orden,
                'REGIS',
                lote_orden);

        SET total_creadas = total_creadas + 1;

    END WHILE;

    SELECT p_folio            AS folio,
           total_creadas      AS laptops_creadas,
           total_existentes   AS laptops_previas,
           total_planificadas AS cant_planificada;
END$$


-- ============================================================
-- 4. sp_Dashboard_Resumen
-- ============================================================
--
-- Objetivo : Devolver en un solo renglón los números del dashboard de
--            administrador para un rango de fechas.
--
-- Parámetros:
--   p_desde  Primer día del rango. NULL = desde que existe la planta.
--   p_hasta  Último día del rango. NULL = hasta hoy.
--
-- ADVERTENCIA — éste no es como los otros tres
-- --------------------------------------------
-- Los de arriba existen porque tocan muchas filas de varias tablas y tienen
-- que pasar o no pasar completas. Éste no escribe nada: solamente lee. No hay
-- transacción que proteger ni atomicidad que ganar.
--
-- El dashboard NO lo usa. El panel de administrador se sirve de las vistas
-- vista_dash_* (DB/vistas.sql), que Django mapea con modelos managed=False y
-- que la API puede filtrar, ordenar y paginar como cualquier otra consulta.
-- Un procedimiento devuelve un conjunto de tuplas suelto: se lee con
-- cursor.callproc(), no pasa por un serializer y no se le puede encadenar nada.
--
-- Entonces, ¿para qué está? Para tener a la mano la versión "un solo CALL con
-- el rango como parámetro", que es lo que una vista no puede hacer (en MySQL
-- las vistas no reciben parámetros). Sirve para demostrarlo y para consultarlo
-- desde la consola:
--
--     CALL sp_Dashboard_Resumen('2026-07-01', '2026-07-31');
--     CALL sp_Dashboard_Resumen(NULL, NULL);   -- todo el histórico
--
-- Si algún día se decide que el dashboard corra sobre procedimientos, éste es
-- el punto de partida; mientras tanto, la fuente de verdad son las vistas.
--
-- Qué cuenta como producida: la laptop embalada, igual que en las vistas y
-- que en tg_Control_Estado_Orden_Produccion.

CREATE PROCEDURE sp_Dashboard_Resumen(
    IN p_desde DATE,
    IN p_hasta DATE
)
BEGIN
    -- Rango abierto por cualquiera de los dos lados. '1000-01-01' es el
    -- mínimo que admite un DATE en MySQL, así que sirve de "sin límite".
    DECLARE desde DATE DEFAULT IFNULL(p_desde, '1000-01-01');
    DECLARE hasta DATE DEFAULT IFNULL(p_hasta, CURDATE());

    SELECT
        desde AS rango_desde,
        hasta AS rango_hasta,

        (SELECT IFNULL(SUM(total), 0)
           FROM vista_dash_produccion_diaria
          WHERE fecha BETWEEN desde AND hasta)          AS producidas,

        (SELECT IFNULL(SUM(total), 0)
           FROM vista_dash_calidad_diaria
          WHERE fecha BETWEEN desde AND hasta)          AS inspecciones,

        (SELECT IFNULL(SUM(aprobadas), 0)
           FROM vista_dash_calidad_diaria
          WHERE fecha BETWEEN desde AND hasta)          AS inspecciones_aprobadas,

        (SELECT IFNULL(SUM(rechazadas), 0)
           FROM vista_dash_calidad_diaria
          WHERE fecha BETWEEN desde AND hasta)          AS inspecciones_rechazadas,

        (SELECT IFNULL(SUM(total), 0)
           FROM vista_dash_paros_diaria
          WHERE fecha BETWEEN desde AND hasta)          AS paros,

        (SELECT IFNULL(SUM(minutos), 0)
           FROM vista_dash_paros_diaria
          WHERE fecha BETWEEN desde AND hasta)          AS paros_minutos,

        (SELECT COUNT(*)
           FROM orden_produccion
          WHERE fecha BETWEEN desde AND hasta)          AS ordenes_creadas;
END$$


DELIMITER ;
