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
    DECLARE v_destino    VARCHAR(8);
    DECLARE v_existe     INT;
    DECLARE v_liberados  INT DEFAULT 0;
    DECLARE v_mermados   INT DEFAULT 0;
    DECLARE v_cerrados   INT DEFAULT 0;

    SET v_destino = IFNULL(p_estado_destino, 'EDC001');

    -- Validaciones

    SELECT COUNT(*) INTO v_existe FROM laptop WHERE numero = p_laptop;

    IF v_existe = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Liberar_Componentes_Laptop: esa laptop no existe';
    END IF;

    IF v_destino NOT IN ('EDC001', 'EDC003') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Liberar_Componentes_Laptop: los componentes solo pueden regresar a Disponible o Dañado';
    END IF;

    -- Cuántos se van a quedar como están, para reportarlo
    SELECT COUNT(*)
      INTO v_mermados
      FROM componente c
      JOIN registro_ensamblaje re ON re.numero = c.registro_ensamblaje
     WHERE re.laptop = p_laptop
       AND c.estado  = 'EDC004';

    -- Soltar los componentes montados.
    -- El estado admite nulos, así que se compara con IS NULL OR <>: un
    -- 'NULL <> EDC004' no es TRUE, es NULL, y esas filas se quedarían fuera.
    UPDATE componente c
      JOIN registro_ensamblaje re ON re.numero = c.registro_ensamblaje
       SET c.estado              = v_destino,
           c.registro_ensamblaje = NULL
     WHERE re.laptop = p_laptop
       AND (c.estado IS NULL OR c.estado <> 'EDC004');

    SET v_liberados = ROW_COUNT();

    -- Cerrar los ensamblajes que siguieran abiertos
    UPDATE registro_ensamblaje
       SET fecha_fin = CURDATE(),
           hora_fin  = CURTIME()
     WHERE laptop    = p_laptop
       AND fecha_fin IS NULL;

    SET v_cerrados = ROW_COUNT();

    SELECT p_laptop    AS laptop,
           v_liberados AS componentes_liberados,
           v_destino   AS estado_destino,
           v_mermados  AS mermados_conservados,
           v_cerrados  AS ensamblajes_cerrados;
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
    DECLARE v_estado     VARCHAR(8);
    DECLARE v_liberados  INT DEFAULT 0;
    DECLARE v_rechazadas INT DEFAULT 0;
    DECLARE v_intactas   INT DEFAULT 0;

    -- Validaciones

    SELECT estado INTO v_estado
      FROM orden_produccion
     WHERE folio = p_folio;

    IF v_estado IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Cancelar_Orden_Produccion: esa orden no existe o no tiene estado';
    END IF;

    IF v_estado = 'CANC' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Cancelar_Orden_Produccion: esa orden ya estaba cancelada';
    END IF;

    IF v_estado = 'COMP' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Cancelar_Orden_Produccion: esa orden ya se completó, no se puede cancelar';
    END IF;

    -- Cuántas laptops terminadas se van a respetar, para reportarlo
    SELECT COUNT(*)
      INTO v_intactas
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

    SET v_liberados = ROW_COUNT();

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

    SET v_rechazadas = ROW_COUNT();

    -- 3. La orden queda cancelada
    UPDATE orden_produccion
       SET estado = 'CANC'
     WHERE folio  = p_folio;

    SELECT p_folio      AS folio,
           v_rechazadas AS laptops_rechazadas,
           v_intactas   AS laptops_respetadas,
           v_liberados  AS componentes_liberados;
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
--   p_linea  Línea donde se van a ensamblar. Va como parámetro porque
--            orden_produccion NO tiene columna de línea: la línea es de la
--            laptop, no de la orden.
--
-- Qué hace:
--   Crea (cant_planificada - las que ya existen) laptops en estado Registrada,
--   heredando el modelo y el lote de la orden. NO abre el registro de
--   ensamblaje: eso sigue siendo laptop por laptop, cuando de verdad arranca.
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
    IN p_folio INT,
    IN p_linea VARCHAR(8)
)
BEGIN
    DECLARE v_estado       VARCHAR(8);
    DECLARE v_modelo       VARCHAR(8);
    DECLARE v_lote         VARCHAR(8);
    DECLARE v_planificada  INT;
    DECLARE v_existentes   INT;
    DECLARE v_faltantes    INT;
    DECLARE v_consecutivo  INT;
    DECLARE v_creadas      INT DEFAULT 0;
    DECLARE v_existe_linea INT;

    -- Validaciones

    SELECT estado, modelo_laptop, lote, IFNULL(cant_planificada, 0)
      INTO v_estado, v_modelo, v_lote, v_planificada
      FROM orden_produccion
     WHERE folio = p_folio;

    IF v_estado IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Iniciar_Ensamblaje_Orden: esa orden no existe o no tiene estado';
    END IF;

    IF v_estado NOT IN ('PEND', 'PROC') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Iniciar_Ensamblaje_Orden: solo se le pueden agregar laptops a una orden Pendiente o En Proceso';
    END IF;

    IF v_modelo IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Iniciar_Ensamblaje_Orden: la orden no tiene modelo de laptop, no se sabe qué fabricar';
    END IF;

    SELECT COUNT(*) INTO v_existe_linea FROM linea WHERE codigo = p_linea;

    IF v_existe_linea = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Iniciar_Ensamblaje_Orden: esa línea no existe';
    END IF;

    -- Cuántas faltan

    SELECT COUNT(*) INTO v_existentes FROM laptop WHERE orden = p_folio;

    SET v_faltantes = v_planificada - v_existentes;

    IF v_faltantes <= 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error sp_Iniciar_Ensamblaje_Orden: esta orden ya tiene todas las laptops que planificó';
    END IF;

    -- Desde qué consecutivo seguir con las series provisionales
    SELECT IFNULL(MAX(CAST(SUBSTRING(num_serie, 5) AS UNSIGNED)), 0)
      INTO v_consecutivo
      FROM laptop
     WHERE num_serie LIKE 'TMP-%';

    WHILE v_creadas < v_faltantes DO

        SET v_consecutivo = v_consecutivo + 1;

        INSERT INTO laptop (num_serie, descripcion, orden, modelo, estado, linea, lote)
        VALUES (CONCAT('TMP-', LPAD(v_consecutivo, 4, '0')),
                CONCAT('Alta en lote de la orden #', p_folio),
                p_folio,
                v_modelo,
                'REGIS',
                p_linea,
                v_lote);

        SET v_creadas = v_creadas + 1;

    END WHILE;

    SELECT p_folio                    AS folio,
           v_creadas                  AS laptops_creadas,
           v_existentes               AS laptops_previas,
           v_planificada              AS cant_planificada,
           p_linea                    AS linea;
END$$


DELIMITER ;
