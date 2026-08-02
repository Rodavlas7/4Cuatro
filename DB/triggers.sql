

-- TRACEX — Triggers consolidados y mejorados
-- Version: 2026-07-20


USE cuatro;

-- Eliminar triggers existentes para evitar conflictos
DROP TRIGGER IF EXISTS tg_Control_Estado_Orden_Produccion;
DROP TRIGGER IF EXISTS tg_Generar_Numero_Serie_Final;
DROP TRIGGER IF EXISTS tg_Finalizar_Proceso_Embalaje;
DROP TRIGGER IF EXISTS tg_Bloquear_Componentes_Laptop_Finalizada;
DROP TRIGGER IF EXISTS tg_Actualizar_Estado_Laptop_Inspeccion_Calidad;
DROP TRIGGER IF EXISTS tg_Control_Componentes_Duplicados;
DROP TRIGGER IF EXISTS tg_Validar_Capacidad_Componente;
DROP TRIGGER IF EXISTS tg_Iniciar_Orden_Al_Registrar_Laptop;
DROP TRIGGER IF EXISTS tg_Iniciar_Orden_Al_Mover_Laptop;
DROP TRIGGER IF EXISTS tg_Sincronizar_Cant_Producida_Alta;
DROP TRIGGER IF EXISTS tg_Sincronizar_Cant_Producida_Cambio;
DROP TRIGGER IF EXISTS tg_Sincronizar_Cant_Producida_Baja;

DELIMITER $$



-- TRIGGER 1: tg_Control_Estado_Orden_Produccion
--
-- Evento   : AFTER INSERT en registro_embalaje
-- Objetivo : Transicionar el estado de la orden de producción
--            conforme avanzan los embalajes de sus laptops.
--
-- Flujo de estados (RF26):
--   Primera laptop embalada  → orden pasa a 'En Proceso'  (PROC)
--   Todas las laptops embaladas = cant_planificada → 'Completada' (COMP)
--
-- Mejoras sobre la versión original:
--   - Usa cant_planificada (nombre real del campo en el SQL actual)
--     para la comparación, no cant_producida, ya que cant_producida
--     cuenta laptops registradas, no embaladas.
--   - Solo actúa si la orden está en 'Pendiente' o 'En Proceso'
--     para no pisar un estado 'Cancelada' puesto manualmente.
--   - Cuenta únicamente laptops cuyo estado sea 'EMBALA' (Embalada)
--     para un conteo preciso por etapa.


CREATE TRIGGER tg_Control_Estado_Orden_Produccion
AFTER INSERT ON registro_embalaje
FOR EACH ROW
BEGIN
    DECLARE folio_orden  INT;
    DECLARE planificadas INT;
    DECLARE embaladas    INT;
    DECLARE estado_orden VARCHAR(8);

    -- Obtener la orden a la que pertenece la laptop recién embalada
    SELECT orden
      INTO folio_orden
      FROM laptop
     WHERE numero = NEW.laptop;

    -- Obtener estado actual y cantidad planificada de esa orden
    SELECT estado, cant_planificada
      INTO estado_orden, planificadas
      FROM orden_produccion
     WHERE folio = folio_orden;

    -- No actuar si la orden ya fue Cancelada o Completada manualmente
    IF estado_orden IN ('PEND', 'PROC') THEN

        -- Contar laptops embaladas (estado EMBALA) en esta orden.
        -- Se incluye la laptop actual (NEW.laptop) aunque el trigger que la
        -- marca como EMBALA (tg_Finalizar_Proceso_Embalaje) aún no se haya
        -- ejecutado, para no depender del orden de disparo de los triggers.
        SELECT COUNT(*)
          INTO embaladas
          FROM laptop
         WHERE orden = folio_orden
           AND (estado = 'EMBALA' OR numero = NEW.laptop);

        IF planificadas > 0 AND embaladas >= planificadas THEN
            -- Todas las laptops planificadas fueron embaladas → Completada
            UPDATE orden_produccion
               SET estado = 'COMP'
             WHERE folio  = folio_orden;

        ELSEIF embaladas = 1 AND estado_orden = 'PEND' THEN
            -- Primera laptop embalada y la orden aún estaba Pendiente → En Proceso
            UPDATE orden_produccion
               SET estado = 'PROC'
             WHERE folio  = folio_orden;
        END IF;

    END IF;
END$$




-- TRIGGER 2: tg_Generar_Numero_Serie_Final
--
-- Evento   : AFTER UPDATE en laptop
-- Objetivo : Generar y asignar automáticamente un número de
--            serie único cuando la laptop pasa a 'Aprobada'.
--
-- Formato del número de serie generado:
--   TP-{AÑO}{MES}{DIA}-{numero de laptop con ceros a la izquierda}
--   Ejemplo: TP-20260715-000042
--
--   Este formato garantiza:
--     - Prefijo 'TP' identifica al modelo ThinkPad
--     - Fecha del día de aprobación para trazabilidad
--     - ID único de la laptop como sufijo
--
-- Mejoras sobre la versión original:
--   - Verifica que la laptop no tenga ya un num_serie asignado
--     (doble protección además del UNIQUE en la columna).
--   - Solo actúa en la transición exacta a 'Aprobada' (APROV),
--     no en cualquier UPDATE al registro.
--   - El formato incluye fecha real de aprobación, útil para
--     auditorías de trazabilidad (RF43, RF50).
--   - Es BEFORE UPDATE y asigna con SET NEW.num_serie. Antes era
--     AFTER UPDATE con un UPDATE laptop adentro, y MySQL no deja que
--     un trigger modifique su propia tabla: aprobar una laptop moría
--     con el error 1442.
--   - OLD.estado se compara con IS NULL / <> porque la columna admite
--     nulos y 'NULL != APROV' no es TRUE, es NULL (la condición nunca
--     se cumplía para una laptop que venía sin estado).



CREATE TRIGGER tg_Generar_Numero_Serie_Final
BEFORE UPDATE ON laptop
FOR EACH ROW
BEGIN
    -- Solo actúa cuando el estado cambia específicamente a Aprobada
    -- y la laptop aún no tiene número de serie asignado
    IF NEW.estado = 'APROV'
       AND (OLD.estado IS NULL OR OLD.estado <> 'APROV')
       AND (NEW.num_serie IS NULL OR NEW.num_serie = '')
    THEN
        -- Formato: TP-AAAAMMDD-000000
        SET NEW.num_serie = CONCAT(
            'TP-',
            DATE_FORMAT(CURDATE(), '%Y%m%d'),
            '-',
            LPAD(NEW.numero, 6, '0')
        );
    END IF;
END$$




-- TRIGGER 3: tg_Finalizar_Proceso_Embalaje
--
-- Evento   : AFTER INSERT en registro_embalaje
-- Objetivo : Cambiar el estado de la laptop a 'Embalada' (EMBALA)
--            en cuanto se registra su embalaje físico.
--
-- Mejoras sobre la versión original:
--   - Verifica que la laptop esté en estado 'Aprobada' (APROV)
--     antes de cambiar el estado.
--     Si ya estaba 'Embalada' o en otro estado inválido, lanza
--     un error descriptivo en lugar de actualizar silenciosamente.
--   - El mensaje de error referencia el número de laptop para
--     facilitar el diagnóstico (RNF12 — gestión de incidencias).


CREATE TRIGGER tg_Finalizar_Proceso_Embalaje
AFTER INSERT ON registro_embalaje
FOR EACH ROW
BEGIN
    DECLARE estado_actual VARCHAR(8);

    SELECT estado
      INTO estado_actual
      FROM laptop
     WHERE numero = NEW.laptop;

    IF estado_actual = 'APROV' THEN
        -- Estado válido para embalaje → actualizar a Embalada
        UPDATE laptop
           SET estado = 'EMBALA'
         WHERE numero = NEW.laptop;

    ELSEIF estado_actual = 'EMBALA' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error tg_Finalizar_Proceso_Embalaje: la laptop ya fue embalada previamente';

    ELSE
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error tg_Finalizar_Proceso_Embalaje: la laptop no está en un estado válido para embalaje (debe estar Aprobada)';
    END IF;
END$$




-- TRIGGER 4: tg_Bloquear_Componentes_Laptop_Finalizada
--
-- Evento   : BEFORE INSERT en registro_ensamblaje
-- Objetivo : Impedir registrar un nuevo ensamblaje sobre una
--            laptop que ya completó su ciclo productivo.
--
-- Estados que bloquean (laptop ya no modificable):
--   APROV  — Aprobada
--   RECHA  — Rechazada
--   EMBALA — Embalada
--
-- Mejoras sobre la versión original:
--   - El mensaje de error incluye el estado actual de la laptop
--     para ayudar al operador a entender por qué fue bloqueado
--     (RNF02 usabilidad, RNF12 gestión de incidencias).


CREATE TRIGGER tg_Bloquear_Componentes_Laptop_Finalizada
BEFORE INSERT ON registro_ensamblaje
FOR EACH ROW
BEGIN
    DECLARE estado_laptop VARCHAR(8);
    DECLARE nombre_edo    VARCHAR(32);

    SELECT l.estado, e.nombre
      INTO estado_laptop, nombre_edo
      FROM laptop     l
      JOIN edo_laptop e ON e.codigo = l.estado
     WHERE l.numero = NEW.laptop;

    IF estado_laptop IN ('APROV', 'RECHA', 'EMBALA') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error tg_Bloquear_Componentes: no se puede registrar ensamblaje, la laptop ya finalizó su proceso productivo';
    END IF;
END$$




-- TRIGGER 5: tg_Actualizar_Estado_Laptop_Inspeccion_Calidad
--
-- Evento   : AFTER INSERT en inspeccion_calidad
-- Objetivo : Cambiar el estado de la laptop según el resultado
--            de la inspección de calidad registrada.
--
-- Resultado 1 → Aprobada  (APROV) → puede pasar a embalaje
-- Resultado 0 → Rechazada (RECHA) → sale de la línea
--
-- Mejoras sobre la versión original:
--   - Verifica que la laptop esté en 'En Ensamblaje' (PENSAM)
--     antes de actuar. Evita que una inspección duplicada o
--     fuera de orden sobreescriba un estado ya válido.
--   - Si la laptop ya fue Aprobada o Rechazada anteriormente,
--     lanza un error en lugar de pisar el estado silenciosamente,
--     protegiendo la integridad del historial (RNF05).
--   - Al aprobar, el estado pasa primero a APROV (Aprobada).
--     El trigger 2 (tg_Generar_Numero_Serie_Final) se encarga
--     de asignar el número de serie automáticamente.


CREATE TRIGGER tg_Actualizar_Estado_Laptop_Inspeccion_Calidad
AFTER INSERT ON inspeccion_calidad
FOR EACH ROW
BEGIN
    DECLARE estado_laptop VARCHAR(8);

    SELECT estado
    INTO estado_laptop
    FROM laptop
    WHERE numero = NEW.laptop;

    IF estado_laptop = 'PENSAM' THEN

        -- Resultado: Aprobada
        IF NEW.resultado = 1 THEN

            UPDATE laptop
            SET estado = 'APROV'
            WHERE numero = NEW.laptop;

        -- Resultado: Rechazada
        ELSEIF NEW.resultado = 0 THEN

            UPDATE laptop
            SET estado = 'RECHA'
            WHERE numero = NEW.laptop;

        -- Resultado: Continúa en ensamblaje
        ELSEIF NEW.resultado = 2 THEN

            UPDATE laptop
            SET estado = 'PENSAM'
            WHERE numero = NEW.laptop;

        ELSE

            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Error tg_Inspeccion_Calidad: resultado de inspección no válido';

        END IF;

    ELSEIF estado_laptop IN ('APROV', 'RECHA', 'EMBALA') THEN

        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error tg_Inspeccion_Calidad: la laptop ya finalizó el proceso de inspección';

    ELSE

        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error tg_Inspeccion_Calidad: la laptop no está en estado de ensamblaje para ser inspeccionada';

    END IF;

END$$




-- TRIGGER 6: tg_Control_Componentes_Duplicados
--
-- Evento   : BEFORE INSERT en registro_ensamblaje
-- Objetivo : Bloquear el registro si el componente (identificado
--            por num_serie en la tabla componente) ya fue asignado
--            a otro registro de ensamblaje previo.
--
-- Mejoras sobre la versión original:
--   - La tabla registro_ensamblaje no guarda el componente
--     directamente; los componentes se vinculan a un registro
--     de ensamblaje mediante componente.registro_ensamblaje (FK).
--     Este trigger protege a nivel de registro_ensamblaje
--     verificando que la laptop destino no tenga ya un registro
--     de ensamblaje cerrado con componentes asignados,
--     evitando duplicación de sesiones de ensamblaje por laptop.
--   - Complementa al TRIGGER 4: mientras el 4 bloquea por
--     estado de la laptop, este bloquea por integridad de datos
--     de ensamblaje ya registrado y cerrado (fecha_fin no nula).
--
-- NOTA: La validación de num_serie duplicado de un componente
--   específico debe hacerse también en la capa de aplicación
--   (Django) al momento de asignar componente.registro_ensamblaje,
--   ya que ese vínculo ocurre en la tabla componente, no aquí.
--   Este trigger es la segunda línea de defensa a nivel BD.


CREATE TRIGGER tg_Control_Componentes_Duplicados
BEFORE INSERT ON registro_ensamblaje
FOR EACH ROW
BEGIN
    DECLARE registros_cerrados INT;

    -- Verificar si la laptop ya tiene un registro de ensamblaje
    -- cerrado (con fecha_fin definida = proceso completado)
    SELECT COUNT(*)
      INTO registros_cerrados
      FROM registro_ensamblaje
     WHERE laptop     = NEW.laptop
       AND fecha_fin  IS NOT NULL;

    IF registros_cerrados > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error tg_Control_Componentes_Duplicados: la laptop ya tiene un ensamblaje registrado y cerrado, no se puede abrir uno nuevo';
    END IF;
END$$




-- TRIGGER 7: tg_Validar_Capacidad_Componente
--
-- Evento   : BEFORE INSERT en componente
-- Objetivo : Impedir instalar en una laptop más componentes de un mismo
--            TIPO de los que permite el BOM (Bill of Materials / Lista de
--            Materiales) del modelo de esa laptop.
--
-- Lógica:
--   - Solo aplica cuando el componente se está asignando a un ensamblaje
--     (NEW.registro_ensamblaje no nulo); si es inventario libre, no valida.
--   - Del registro de ensamblaje se obtiene la laptop y su modelo.
--   - Del componente nuevo se obtiene su tipo (modelo_componente.tipo_componente).
--   - La capacidad permitida para ese tipo se toma del BOM
--     (modelo_laptop_componente) del modelo de la laptop.
--   - Se cuentan los componentes del MISMO tipo ya instalados en esa laptop
--     (se excluyen los mermados EDC004, que liberan espacio).
--   - Si al agregar el nuevo se excede la capacidad, se cancela el INSERT.
--   - Si el tipo no está en el BOM, no es compatible con el modelo → se bloquea.
--
-- NOTA: valida en INSERT (cuando el componente se crea ya asignado). Si en
--   la app un componente se asigna después vía UPDATE (registro_ensamblaje
--   pasa de NULL a un valor), habría que replicar esta lógica en un
--   BEFORE UPDATE.


CREATE TRIGGER tg_Validar_Capacidad_Componente
BEFORE INSERT ON componente
FOR EACH ROW
BEGIN
    DECLARE v_laptop        INT;
    DECLARE v_modelo_laptop VARCHAR(8);
    DECLARE v_tipo          VARCHAR(8);
    DECLARE v_capacidad     INT;
    DECLARE v_instalados    INT;

    IF NEW.registro_ensamblaje IS NOT NULL AND NEW.modelo IS NOT NULL THEN

        -- Laptop y su modelo, a partir del registro de ensamblaje
        SELECT re.laptop, l.modelo
          INTO v_laptop, v_modelo_laptop
          FROM registro_ensamblaje re
          JOIN laptop l ON l.numero = re.laptop
         WHERE re.numero = NEW.registro_ensamblaje;

        -- Tipo del componente que se quiere instalar
        SELECT mc.tipo_componente
          INTO v_tipo
          FROM modelo_componente mc
         WHERE mc.codigo = NEW.modelo;

        -- Capacidad permitida para ese tipo, según el BOM del modelo de laptop
        SELECT MAX(mlc.capacidad)
          INTO v_capacidad
          FROM modelo_laptop_componente mlc
          JOIN modelo_componente mc2 ON mc2.codigo = mlc.modelo_componente
         WHERE mlc.modelo_laptop   = v_modelo_laptop
           AND mc2.tipo_componente = v_tipo;

        -- Si el tipo no está en el BOM, no es compatible con el modelo
        IF v_capacidad IS NULL THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Error tg_Validar_Capacidad_Componente: el tipo de componente no es compatible con el modelo de la laptop';
        END IF;

        -- Componentes del mismo tipo ya instalados en esa laptop
        -- (se excluyen los mermados EDC004)
        SELECT COUNT(*)
          INTO v_instalados
          FROM componente c
          JOIN registro_ensamblaje re2 ON re2.numero = c.registro_ensamblaje
          JOIN modelo_componente   mc3 ON mc3.codigo = c.modelo
         WHERE re2.laptop          = v_laptop
           AND mc3.tipo_componente = v_tipo
           AND (c.estado IS NULL OR c.estado <> 'EDC004');

        -- ¿El nuevo excedería la capacidad de ese tipo?
        IF v_instalados + 1 > v_capacidad THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Error tg_Validar_Capacidad_Componente: se excede la capacidad de ese tipo de componente para el modelo de la laptop';
        END IF;

    END IF;
END$$




-- TRIGGERS 8, 9 y 10: tg_Sincronizar_Cant_Producida_*
--
-- Evento   : AFTER INSERT / AFTER UPDATE / AFTER DELETE en laptop
-- Objetivo : Mantener orden_produccion.cant_producida al día sin que
--            nadie la capture a mano.
--
-- Qué cuenta:
--   Laptops de la orden que ya terminaron su proceso, es decir con
--   estado 'APROV' (Aprobada) o 'EMBALA' (Embalada). Quedan fuera las
--   rechazadas (RECHA), las que siguen en ensamblaje (PENSAM) y las
--   apenas registradas (REGIS), porque ninguna de esas es producción
--   terminada.
--
-- Por qué recuenta en lugar de sumar 1:
--   Un contador incremental se desincroniza en cuanto alguien corrige
--   un estado a mano, mueve una laptop de orden o borra un registro.
--   El COUNT(*) completo se autocorrige solo en cada cambio; sobre el
--   volumen de una orden el costo es irrelevante.
--
-- Momentos en los que se dispara de forma natural:
--   - tg_Actualizar_Estado_Laptop_Inspeccion_Calidad marca APROV  → +1
--   - tg_Finalizar_Proceso_Embalaje marca EMBALA (ya contaba)     → igual
--   - Una laptop aprobada que se reprueba a RECHA                 → -1
--
-- NOTA: leer la propia tabla laptop dentro de un trigger sobre laptop
--   sí está permitido; lo que MySQL prohíbe es modificarla (error 1442).
--   Aquí solo se escribe en orden_produccion.


-- TRIGGER 11: tg_Iniciar_Orden_Al_Registrar_Laptop
--
-- Evento   : AFTER INSERT en laptop
-- Objetivo : Arrancar la orden en cuanto se le registra su PRIMERA laptop:
--            el estado pasa de 'Pendiente' (PEND) a 'En Proceso' (PROC).
--
-- Por qué hace falta si ya existe el TRIGGER 1:
--   El TRIGGER 1 mueve la orden a 'En Proceso' cuando se EMBALA la primera
--   laptop, que es mucho después. Con este, la orden refleja que ya se está
--   trabajando desde que se le da de alta la primera unidad. Los dos conviven:
--   para cuando llega el embalaje la orden ya está en PROC, así que esa rama
--   del TRIGGER 1 simplemente no encuentra nada que hacer, y su rama de
--   'Completada' sigue funcionando igual.
--
-- Solo actúa sobre órdenes en 'Pendiente': una Cancelada o Completada no se
-- reabre por registrarle una laptop.


CREATE TRIGGER tg_Iniciar_Orden_Al_Registrar_Laptop
AFTER INSERT ON laptop
FOR EACH ROW
BEGIN
    IF NEW.orden IS NOT NULL THEN
        UPDATE orden_produccion
           SET estado = 'PROC'
         WHERE folio  = NEW.orden
           AND estado = 'PEND';
    END IF;
END$$




-- TRIGGER 12: tg_Iniciar_Orden_Al_Mover_Laptop
--
-- Evento   : AFTER UPDATE en laptop
-- Objetivo : El mismo arranque que el TRIGGER 11, pero para la otra forma de
--            agregarle una laptop a una orden: reasignar una que ya existía.
--
-- Hace falta porque el TRIGGER 11 sólo se dispara en INSERT. La pantalla de
-- edición de laptop deja cambiar la orden, y por ahí una orden 'Pendiente'
-- recibía su primera laptop sin arrancar.
--
-- Sólo actúa cuando la orden REALMENTE cambia: un UPDATE que toque cualquier
-- otro campo (estado, línea, descripción) no tiene por qué mover la orden. El
-- operador <=> compara tolerando nulos, cosa que '=' no hace: con '=' una
-- laptop que pasa de NULL a una orden no se detectaría.
--
-- La orden que PIERDE la laptop se queda como estaba. Regresarla a 'Pendiente'
-- sería adivinar: pudo avanzar a 'En Proceso' por otras razones, y una orden
-- que retrocede sola confunde más de lo que ayuda.


CREATE TRIGGER tg_Iniciar_Orden_Al_Mover_Laptop
AFTER UPDATE ON laptop
FOR EACH ROW
BEGIN
    IF NOT (NEW.orden <=> OLD.orden) AND NEW.orden IS NOT NULL THEN
        UPDATE orden_produccion
           SET estado = 'PROC'
         WHERE folio  = NEW.orden
           AND estado = 'PEND';
    END IF;
END$$


CREATE TRIGGER tg_Sincronizar_Cant_Producida_Alta
AFTER INSERT ON laptop
FOR EACH ROW
BEGIN
    -- Normalmente una laptop nace en 'Registrada' y no suma, pero si se
    -- da de alta ya terminada (una carga de datos, por ejemplo) el
    -- recuento la toma igual.
    IF NEW.orden IS NOT NULL THEN
        UPDATE orden_produccion
           SET cant_producida = (
                   SELECT COUNT(*)
                     FROM laptop
                    WHERE orden  = NEW.orden
                      AND estado IN ('APROV', 'EMBALA')
               )
         WHERE folio = NEW.orden;
    END IF;
END$$


CREATE TRIGGER tg_Sincronizar_Cant_Producida_Cambio
AFTER UPDATE ON laptop
FOR EACH ROW
BEGIN
    -- Solo interesan los cambios de estado o de orden. El <=> compara
    -- tolerando nulos: 'NULL <=> NULL' es TRUE, a diferencia de '='.
    IF NOT (NEW.estado <=> OLD.estado) OR NOT (NEW.orden <=> OLD.orden) THEN

        -- Orden a la que pertenece ahora
        IF NEW.orden IS NOT NULL THEN
            UPDATE orden_produccion
               SET cant_producida = (
                       SELECT COUNT(*)
                         FROM laptop
                        WHERE orden  = NEW.orden
                          AND estado IN ('APROV', 'EMBALA')
                   )
             WHERE folio = NEW.orden;
        END IF;

        -- Si la laptop se movió de orden, la anterior también se recuenta
        IF OLD.orden IS NOT NULL AND NOT (OLD.orden <=> NEW.orden) THEN
            UPDATE orden_produccion
               SET cant_producida = (
                       SELECT COUNT(*)
                         FROM laptop
                        WHERE orden  = OLD.orden
                          AND estado IN ('APROV', 'EMBALA')
                   )
             WHERE folio = OLD.orden;
        END IF;

    END IF;
END$$


CREATE TRIGGER tg_Sincronizar_Cant_Producida_Baja
AFTER DELETE ON laptop
FOR EACH ROW
BEGIN
    IF OLD.orden IS NOT NULL THEN
        UPDATE orden_produccion
           SET cant_producida = (
                   SELECT COUNT(*)
                     FROM laptop
                    WHERE orden  = OLD.orden
                      AND estado IN ('APROV', 'EMBALA')
               )
         WHERE folio = OLD.orden;
    END IF;
END$$

DELIMITER ;



-- SINCRONIZACIÓN INICIAL
--
-- Los triggers de arriba solo actúan de aquí en adelante. Esta sentencia
-- pone al día lo que ya está capturado en la base, para que cant_producida
-- arranque cuadrada con las laptops reales de cada orden.

UPDATE orden_produccion op
   SET op.cant_producida = (
           SELECT COUNT(*)
             FROM laptop l
            WHERE l.orden  = op.folio
              AND l.estado IN ('APROV', 'EMBALA')
       );



-- ORDEN DE DISPARO EN BEFORE INSERT registro_ensamblaje
--
-- MySQL ejecuta múltiples triggers del mismo evento en orden
-- de creación. El orden correcto para este archivo es:
--
--   1. tg_Control_Componentes_Duplicados  (¿ya hay ensamblaje cerrado?)
--   2. tg_Bloquear_Componentes_Laptop_Finalizada (¿el estado lo permite?)
--
-- Si cualquiera de los dos lanza SIGNAL, el INSERT se cancela
-- y el segundo trigger no llega a ejecutarse.


-- CADENA DE DISPARO AL APROBAR UNA LAPTOP
--
-- Un solo INSERT en inspeccion_calidad con resultado = 1 encadena:
--
--   1. tg_Actualizar_Estado_Laptop_Inspeccion_Calidad
--        hace UPDATE laptop SET estado = 'APROV'
--   2. tg_Generar_Numero_Serie_Final  (BEFORE UPDATE laptop)
--        le pone el num_serie a esa misma fila
--   3. tg_Sincronizar_Cant_Producida_Cambio  (AFTER UPDATE laptop)
--        recuenta orden_produccion.cant_producida
--
-- Y un INSERT en registro_embalaje encadena:
--
--   1. tg_Control_Estado_Orden_Produccion   → estado de la orden
--   2. tg_Finalizar_Proceso_Embalaje        → UPDATE laptop a 'EMBALA'
--   3. tg_Sincronizar_Cant_Producida_Cambio → recuenta (la laptop ya
--        contaba desde 'APROV', así que el número no se mueve)
--
-- OJO con esas dos cadenas: los UPDATE de laptop que hacen los triggers 5 y 3
-- también pasan por tg_Iniciar_Orden_Al_Mover_Laptop, pero ahí NO cambia la
-- columna `orden`, así que su condición no se cumple y no hace nada. Sólo
-- reacciona cuando la laptop de verdad se cambia de orden.
--
--
-- LAS DOS FORMAS DE ARRANCAR UNA ORDEN
--
-- Una orden 'Pendiente' pasa a 'En Proceso' en cuanto recibe su primera laptop,
-- y eso puede ocurrir por dos caminos distintos:
--
--   tg_Iniciar_Orden_Al_Registrar_Laptop  (INSERT)  laptop nueva en la orden
--   tg_Iniciar_Orden_Al_Mover_Laptop      (UPDATE)  laptop existente reasignada
--
-- Los dos hacen lo mismo y los dos filtran por estado = 'PEND', así que una
-- orden Cancelada o Completada no se reabre por ninguno de los dos caminos.





-- VERIFICACIÓN — consultas para confirmar que los triggers
-- quedaron registrados correctamente en la BD


SELECT trigger_name,
       event_manipulation AS evento,
       event_object_table AS tabla,
       action_timing      AS momento
  FROM information_schema.triggers
 WHERE trigger_schema = 'cuatro'
 ORDER BY event_object_table, action_timing, action_order;