-- Active: 1783038914702@@localhost@3306@cuatro

-- TRACEX — Datos de prueba (transaccionales)
-- Version: 2026-07-21
--
-- Objetivo : Poblar las tablas transaccionales con datos suficientes para
--            probar TODAS las URLs y funcionalidades de la API.
--
-- REQUISITOS (ejecutar en este orden ANTES que este archivo):
--   1) estructura.sql   -- tablas
--   2) datos.sql        -- catálogos + BOM (modelo_laptop_componente)
--   3) triggers.sql     -- triggers
--
-- Este archivo asume que los catálogos (roles, turnos, estados, tipos,
-- modelos, líneas, estaciones, empleados, lotes y el BOM) YA existen, y
-- solo agrega datos transaccionales encima.
--
-- Los datos se insertan siguiendo el flujo real de producción para no
-- chocar con los triggers (una laptop entra en ENSAMBLAJE, se le registra
-- el ensamblaje y sus componentes, pasa por inspección y luego embalaje).


USE cuatro;


-- ============================================================
--  LIMPIEZA (solo tablas transaccionales; NO toca catálogos ni BOM)
-- ============================================================
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE componente;
TRUNCATE TABLE detalle_material;
TRUNCATE TABLE inspeccion_calidad;
TRUNCATE TABLE registro_embalaje;
TRUNCATE TABLE registro_ensamblaje;
TRUNCATE TABLE paro;
TRUNCATE TABLE laptop;
TRUNCATE TABLE orden_material;
TRUNCATE TABLE orden_produccion;
SET FOREIGN_KEY_CHECKS = 1;


-- ============================================================
--  1. ÓRDENES DE PRODUCCIÓN  (estados PEND / PROC / CANC; la COMP la
--     dejará el trigger de embalaje automáticamente en la orden 3)
-- ============================================================
INSERT INTO orden_produccion (fecha, hora, modelo_laptop, cant_planificada, cant_producida, estado) VALUES
('2026-07-21', '08:00:00', 'ML001', 5, 0, 'PEND'),   -- folio 1
('2026-07-21', '09:00:00', 'ML001', 3, 2, 'PROC'),   -- folio 2
('2026-07-20', '08:00:00', 'ML001', 1, 1, 'PROC'),   -- folio 3 (pasará a COMP por trigger)
('2026-07-19', '08:00:00', 'ML001', 2, 0, 'CANC');   -- folio 4


-- ============================================================
--  2. LAPTOPS  (se crean en su estado de trabajo: REGIS o PENSAM.
--     Las que terminan APROV/RECHA/EMBALA pasan por inspección/embalaje
--     más abajo. num_serie es UNIQUE, por eso cada una es distinta.)
-- ============================================================
INSERT INTO laptop (num_serie, descripcion, orden, modelo, estado, linea, lote) VALUES
('TMP-0001', 'Unidad 1 - recién registrada',          1, 'ML001', 'REGIS',  'LIN001', 'LOT2026A'),  -- numero 1
('TMP-0002', 'Unidad 2 - en ensamblaje (completa)',   1, 'ML001', 'PENSAM', 'LIN001', 'LOT2026A'),  -- numero 2
('TMP-0003', 'Unidad 3 - en ensamblaje (parcial)',    1, 'ML001', 'PENSAM', 'LIN002', 'LOT2026A'),  -- numero 3
('TP-20260721-000004', 'Unidad 4 - será aprobada',    2, 'ML001', 'PENSAM', 'LIN001', 'LOT2026A'),  -- numero 4
('TMP-0005', 'Unidad 5 - será rechazada',             2, 'ML001', 'PENSAM', 'LIN001', 'LOT2026A'),  -- numero 5
('TMP-0006', 'Unidad 6 - en ensamblaje',              2, 'ML001', 'PENSAM', 'LIN003', 'LOT2026A'),  -- numero 6
('TP-20260721-000007', 'Unidad 7 - será embalada',    3, 'ML001', 'PENSAM', 'LIN001', 'LOT2026A'),  -- numero 7
('TMP-0008', 'Unidad 8 - de orden cancelada',         4, 'ML001', 'REGIS',  'LIN001', 'LOT2026A');  -- numero 8


-- ============================================================
--  3. REGISTROS DE ENSAMBLAJE  (para las laptops 2,3,4,5,6,7)
--     Se insertan mientras la laptop está en PENSAM (los triggers
--     BEFORE INSERT lo permiten en ese estado).
--     Abiertos = fecha_fin NULL ; Cerrados = fecha_fin con valor.
-- ============================================================
INSERT INTO registro_ensamblaje (fecha_inicio, fecha_fin, hora_inicio, hora_fin, laptop, linea) VALUES
('2026-07-21', NULL,         '08:10:00', NULL,        2, 'LIN001'),  -- registro 1 (L2, abierto)
('2026-07-21', NULL,         '08:15:00', NULL,        3, 'LIN002'),  -- registro 2 (L3, abierto)
('2026-07-21', '2026-07-21', '08:00:00', '10:00:00',  4, 'LIN001'),  -- registro 3 (L4, cerrado)
('2026-07-21', '2026-07-21', '08:05:00', '09:30:00',  5, 'LIN001'),  -- registro 4 (L5, cerrado)
('2026-07-21', NULL,         '08:20:00', NULL,        6, 'LIN003'),  -- registro 5 (L6, abierto)
('2026-07-20', '2026-07-20', '08:00:00', '11:00:00',  7, 'LIN001');  -- registro 6 (L7, cerrado)


-- ============================================================
--  4. COMPONENTES INSTALADOS  (asignados a un registro_ensamblaje).
--     El trigger tg_Validar_Capacidad_Componente valida que no se
--     exceda la capacidad por TIPO del BOM (CPU 1, RAM 2, SSD 2, resto 1).
-- ============================================================
-- L2 (registro 1) — juego completo
INSERT INTO componente (num_serie, descripcion, linea, modelo, lote, estado, registro_ensamblaje) VALUES
('CMP-L2-CPU', 'Procesador',    'LIN001', 'MC001', 'LCOMP-001', 'EDC002', 1),
('CMP-L2-RAM1','RAM módulo 1',  'LIN001', 'MC005', 'LCOMP-001', 'EDC002', 1),
('CMP-L2-RAM2','RAM módulo 2',  'LIN001', 'MC006', 'LCOMP-001', 'EDC002', 1),
('CMP-L2-SSD', 'SSD',           'LIN001', 'MC009', 'LCOMP-001', 'EDC002', 1),
('CMP-L2-MB',  'Tarjeta madre', 'LIN001', 'MC012', 'LCOMP-001', 'EDC002', 1),
('CMP-L2-BAT', 'Batería',       'LIN001', 'MC017', 'LCOMP-001', 'EDC002', 1);

-- L3 (registro 2) — parcial
INSERT INTO componente (num_serie, descripcion, linea, modelo, lote, estado, registro_ensamblaje) VALUES
('CMP-L3-CPU', 'Procesador',   'LIN002', 'MC001', 'LCOMP-001', 'EDC002', 2),
('CMP-L3-RAM1','RAM módulo 1', 'LIN002', 'MC005', 'LCOMP-001', 'EDC002', 2);

-- L4 (registro 3) — juego completo (Intel)
INSERT INTO componente (num_serie, descripcion, linea, modelo, lote, estado, registro_ensamblaje) VALUES
('CMP-L4-CPU', 'Procesador',    'LIN001', 'MC002', 'LCOMP-002', 'EDC002', 3),
('CMP-L4-RAM1','RAM módulo 1',  'LIN001', 'MC005', 'LCOMP-002', 'EDC002', 3),
('CMP-L4-RAM2','RAM módulo 2',  'LIN001', 'MC007', 'LCOMP-002', 'EDC002', 3),
('CMP-L4-SSD', 'SSD',           'LIN001', 'MC010', 'LCOMP-002', 'EDC002', 3),
('CMP-L4-MB',  'Tarjeta madre', 'LIN001', 'MC013', 'LCOMP-002', 'EDC002', 3),
('CMP-L4-BAT', 'Batería',       'LIN001', 'MC017', 'LCOMP-002', 'EDC002', 3);

-- L5 (registro 4) — parcial
INSERT INTO componente (num_serie, descripcion, linea, modelo, lote, estado, registro_ensamblaje) VALUES
('CMP-L5-CPU', 'Procesador', 'LIN001', 'MC001', 'LCOMP-001', 'EDC002', 4),
('CMP-L5-SSD', 'SSD',        'LIN001', 'MC009', 'LCOMP-001', 'EDC002', 4);

-- L6 (registro 5) — parcial
INSERT INTO componente (num_serie, descripcion, linea, modelo, lote, estado, registro_ensamblaje) VALUES
('CMP-L6-CPU', 'Procesador',   'LIN003', 'MC003', 'LCOMP-002', 'EDC002', 5),
('CMP-L6-RAM1','RAM módulo 1', 'LIN003', 'MC006', 'LCOMP-002', 'EDC002', 5);

-- L7 (registro 6) — juego completo
INSERT INTO componente (num_serie, descripcion, linea, modelo, lote, estado, registro_ensamblaje) VALUES
('CMP-L7-CPU', 'Procesador',    'LIN001', 'MC001', 'LCOMP-001', 'EDC002', 6),
('CMP-L7-RAM1','RAM módulo 1',  'LIN001', 'MC005', 'LCOMP-001', 'EDC002', 6),
('CMP-L7-RAM2','RAM módulo 2',  'LIN001', 'MC006', 'LCOMP-001', 'EDC002', 6),
('CMP-L7-SSD', 'SSD',           'LIN001', 'MC009', 'LCOMP-001', 'EDC002', 6),
('CMP-L7-MB',  'Tarjeta madre', 'LIN001', 'MC012', 'LCOMP-001', 'EDC002', 6),
('CMP-L7-BAT', 'Batería',       'LIN001', 'MC017', 'LCOMP-001', 'EDC002', 6);


-- ============================================================
--  5. COMPONENTES EN INVENTARIO  (sin ensamblaje asignado; el trigger
--     de capacidad NO aplica). Distintos estados para variedad.
-- ============================================================
INSERT INTO componente (num_serie, descripcion, linea, modelo, lote, estado, registro_ensamblaje) VALUES
('INV-CPU-01', 'Procesador en inventario', 'LIN001', 'MC004', 'LCOMP-002', 'EDC001', NULL),
('INV-SSD-01', 'SSD en inventario',        'LIN001', 'MC008', 'LCOMP-001', 'EDC001', NULL),
('INV-PAN-01', 'Pantalla en inventario',   'LIN001', 'MC014', 'LCOMP-001', 'EDC001', NULL),
('INV-KB-01',  'Teclado en inventario',    'LIN002', 'MC018', 'LCOMP-001', 'EDC001', NULL),
('INV-WIFI-01','Wi-Fi en inventario',      'LIN002', 'MC024', 'LCOMP-002', 'EDC001', NULL),
('INV-CAM-01', 'Cámara dañada',            'LIN003', 'MC022', 'LCOMP-001', 'EDC003', NULL);


-- ============================================================
--  6. INSPECCIONES DE CALIDAD  (dispara el cambio de estado de la laptop)
--     L4 -> Aprobada (resultado 1) ; L5 -> Rechazada (resultado 0)
--     L7 -> Aprobada (resultado 1, luego se embala abajo)
-- ============================================================
INSERT INTO inspeccion_calidad (resultado, observaciones, fecha, hora, laptop, empleado, linea) VALUES
(1, 'Todo en orden, aprobada',          '2026-07-21', '10:30:00', 4, 2607004, 'LIN001'),
(0, 'Falla en pantalla, rechazada',     '2026-07-21', '09:45:00', 5, 2607004, 'LIN001'),
(1, 'Cumple especificaciones, aprobada','2026-07-20', '11:30:00', 7, 2607004, 'LIN001');


-- ============================================================
--  7. EMBALAJE  (laptop 7, que quedó APROV, se embala)
--     El trigger la pasa a EMBALA y, como la orden 3 tenía planificada 1
--     y esta es su única laptop embalada, la orden 3 pasa a COMPLETADA.
-- ============================================================
INSERT INTO registro_embalaje (fecha, hora, laptop, tipo) VALUES
('2026-07-20', '12:00:00', 7, 'TE001');


-- ============================================================
--  8. ÓRDENES DE MATERIAL + SUS RENGLONES (detalle_material, PK compuesta)
-- ============================================================
INSERT INTO orden_material (fecha, hora, linea) VALUES
('2026-07-21', '07:30:00', 'LIN001'),   -- numero 1
('2026-07-21', '07:45:00', 'LIN002');   -- numero 2

INSERT INTO detalle_material (orden, modelo, cantidad) VALUES
(1, 'MC001',  50),
(1, 'MC005', 100),
(1, 'MC009',  30),
(2, 'MC002',  20),
(2, 'MC006',  40);


-- ============================================================
--  9. PAROS  (abiertos = fecha_fin NULL ; cerrados = con fecha_fin)
-- ============================================================
INSERT INTO paro (razon, fecha_inicio, fecha_fin, hora_inicio, hora_fin, linea) VALUES
('Falla en banda transportadora',      '2026-07-21', NULL,         '09:00:00', NULL,        'LIN001'),
('Mantenimiento preventivo programado','2026-07-20', '2026-07-20', '14:00:00', '15:30:00',  'LIN002'),
('Falta de suministro de componentes', '2026-07-21', NULL,         '10:15:00', NULL,        'LIN003');


-- ============================================================
--  VERIFICACIÓN — resumen de lo insertado
-- ============================================================
SELECT 'orden_produccion' AS tabla, COUNT(*) AS filas FROM orden_produccion
UNION ALL SELECT 'laptop',              COUNT(*) FROM laptop
UNION ALL SELECT 'registro_ensamblaje', COUNT(*) FROM registro_ensamblaje
UNION ALL SELECT 'componente',          COUNT(*) FROM componente
UNION ALL SELECT 'inspeccion_calidad',  COUNT(*) FROM inspeccion_calidad
UNION ALL SELECT 'registro_embalaje',   COUNT(*) FROM registro_embalaje
UNION ALL SELECT 'orden_material',      COUNT(*) FROM orden_material
UNION ALL SELECT 'detalle_material',    COUNT(*) FROM detalle_material
UNION ALL SELECT 'paro',                COUNT(*) FROM paro;

-- Estados finales de laptops (deberían verse REGIS, PENSAM, APROV, RECHA, EMBALA)
SELECT numero, num_serie, estado FROM laptop ORDER BY numero;

-- Estados finales de órdenes (la 3 debe estar COMP por el trigger de embalaje)
SELECT folio, estado, cant_planificada FROM orden_produccion ORDER BY folio;
