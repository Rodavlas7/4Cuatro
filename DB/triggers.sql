

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

DELIMITER $$



-- TRIGGER 1: tg_Control_Estado_Orden_Produccion
--
-- Evento   : AFTER INSERT en registro_embalaje
-- Objetivo : Transicionar el estado de la orden de producción
--            conforme avanzan los embalajes de sus laptops.
--
-- Flujo de estados (RF26):
--   Primera laptop embalada  → orden pasa a 'En Proceso'  (PROC)
--   Todas las laptops embaladas = cant_planificda → 'Completada' (COMP)
--
-- Mejoras sobre la versión original:
--   - Usa cant_planificda (nombre real del campo en el SQL actual)
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
    SELECT estado, cant_planificda
      INTO estado_orden, planificadas
      FROM orden_produccion
     WHERE folio = folio_orden;

    -- No actuar si la orden ya fue Cancelada o Completada manualmente
    IF estado_orden IN ('PEND', 'PROC') THEN

        -- Contar laptops embaladas (estado EMBALA) en esta orden
        SELECT COUNT(*)
          INTO embaladas
          FROM laptop
         WHERE orden  = folio_orden
           AND estado = 'EMBALA';

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



CREATE TRIGGER tg_Generar_Numero_Serie_Final
AFTER UPDATE ON laptop
FOR EACH ROW
BEGIN
    DECLARE serie_final VARCHAR(50);

    -- Solo actúa cuando el estado cambia específicamente a Aprobada
    -- y la laptop aún no tiene número de serie asignado
    IF NEW.estado = 'APROV'
       AND OLD.estado != 'APROV'
       AND (NEW.num_serie IS NULL OR NEW.num_serie = '')
    THEN
        -- Formato: TP-AAAAMMDD-000000
        SET serie_final = CONCAT(
            'TP-',
            DATE_FORMAT(CURDATE(), '%Y%m%d'),
            '-',
            LPAD(NEW.numero, 6, '0')
        );

        UPDATE laptop
           SET num_serie = serie_final
         WHERE numero    = NEW.numero;
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
        -- Laptop en ensamblaje: estado válido para inspección
        IF NEW.resultado = 1 THEN
            UPDATE laptop SET estado = 'APROV' WHERE numero = NEW.laptop;
        ELSE
            UPDATE laptop SET estado = 'RECHA' WHERE numero = NEW.laptop;
        END IF;

    ELSEIF estado_laptop IN ('APROV', 'RECHA') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error tg_Inspeccion_Calidad: la laptop ya cuenta con una inspección registrada';

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

DELIMITER ;



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





-- VERIFICACIÓN — consultas para confirmar que los triggers
-- quedaron registrados correctamente en la BD


SELECT trigger_name,
       event_manipulation AS evento,
       event_object_table AS tabla,
       action_timing      AS momento
  FROM information_schema.triggers
 WHERE trigger_schema = 'cuatro'
 ORDER BY event_object_table, action_timing, action_order;