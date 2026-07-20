-- Active: 1784571729921@@127.0.0.1@3306@cuatro

-- TRACEX — Catálogo inicial de datos
-- Laptop: Lenovo ThinkPad T14 Gen 5
-- Version: 2026-07-15


USE cuatro;


-- Desactivar validación de FKs para poder borrar en cualquier orden
SET FOREIGN_KEY_CHECKS = 0;
 
TRUNCATE TABLE componente;
TRUNCATE TABLE detalle_material;
TRUNCATE TABLE inspeccion_calidad;
TRUNCATE TABLE registro_embalaje;
TRUNCATE TABLE registro_ensamblaje;
TRUNCATE TABLE paro;
TRUNCATE TABLE laptop;
TRUNCATE TABLE lote_laptop;
TRUNCATE TABLE lote_comp;
TRUNCATE TABLE orden_material;
TRUNCATE TABLE orden_produccion;
TRUNCATE TABLE empleado_estacion;
TRUNCATE TABLE empleado_linea;
TRUNCATE TABLE estacion;
TRUNCATE TABLE linea;
TRUNCATE TABLE sesion;
TRUNCATE TABLE usuario;
TRUNCATE TABLE empleado;
TRUNCATE TABLE modelo_componente;
TRUNCATE TABLE modelo_laptop;
TRUNCATE TABLE tipo_comp;
TRUNCATE TABLE tipo_embalaje;
TRUNCATE TABLE edo_componente;
TRUNCATE TABLE edo_laptop;
TRUNCATE TABLE edo_linea;
TRUNCATE TABLE edo_produccion;
TRUNCATE TABLE rol;
TRUNCATE TABLE turno;
 
-- Reactivar validación de FKs
SET FOREIGN_KEY_CHECKS = 1;

-- 1. ROLES

INSERT INTO rol (codigo, nombre, descripcion) VALUES
('ADMIN', 'Administrador',       'Acceso total al sistema, gestión de usuarios y configuración general'),
('SUPER', 'Supervisor',          'Supervisión de líneas de ensamblaje, asignación de personal y consulta de reportes'),
('OPENSA', 'Operario Ensamblaje', 'Registro de ensamblaje y asociación de componentes en estaciones de trabajo'),
('OPCALI', 'Inspector Calidad',   'Registro y consulta de inspecciones de calidad de laptops'),
('OPEMBA', 'Operario Embalaje',   'Registro del proceso de embalaje y actualización de estado final');


-- 2. TURNOS

INSERT INTO turno (codigo, nombre, hora_entrada, hora_salida) VALUES
('MAT', 'Matutino',   '06:00:00', '14:00:00'),
('VES', 'Vespertino', '14:00:00', '22:00:00');

-- 3. ESTADOS DE LÍNEA

INSERT INTO edo_linea (codigo, nombre, descripcion) VALUES
('ACTI', 'Activa',       'Línea en operación normal'),
('INAC', 'Inactiva',     'Línea fuera de operación temporalmente'),
('PARO', 'En Paro',      'Línea detenida por incidencia registrada'),
('MANT', 'Mantenimiento','Línea en proceso de mantenimiento preventivo o correctivo');


-- 4. ESTADOS DE LAPTOP 

INSERT INTO edo_laptop (codigo, nombre) VALUES
('REGIS', 'Registrada'),       
('PENSAM', 'En Ensamblaje'),    
('PINSPE', 'En Inspección'),    
('APROV', 'Aprobada'),         
('RECHA', 'Rechazada'),        
('PENDEM', 'Pendiente Embalaje'),
('EMBALA', 'Embalada');         


-- 5. ESTADOS DE COMPONENTE

INSERT INTO edo_componente (codigo, nombre, descripcion) VALUES
('EDC001', 'Disponible', 'Componente en inventario listo para ensamblaje'),
('EDC002', 'En Uso',     'Componente asignado e instalado en una laptop'),
('EDC003', 'Dañado',     'Componente con defecto de fábrica o dañado en proceso'),
('EDC004', 'Mermado',    'Componente descartado o perdido');


-- 6. ESTADOS DE PRODUCCIÓN 

INSERT INTO edo_produccion (codigo, nombre) VALUES
('PEND', 'Pendiente'),
('PROC', 'En Proceso'),
('COMP', 'Completada'),
('CANC', 'Cancelada');


-- 7. TIPOS DE COMPONENTE

INSERT INTO tipo_comp (codigo, nombre) VALUES
('TC001', 'Procesador'),
('TC002', 'Memoria RAM'),
('TC003', 'Almacenamiento SSD'),
('TC004', 'Tarjeta Madre'),
('TC005', 'Pantalla'),
('TC006', 'Batería'),
('TC007', 'Teclado'),
('TC008', 'Touchpad'),
('TC009', 'Cámara Web'),
('TC010', 'Tarjeta de Red'),
('TC011', 'Disipador / Ventilador'),
('TC012', 'Chasis Superior'),
('TC013', 'Chasis Inferior'),
('TC014', 'Conector de Carga'),
('TC015', 'Altavoces');


-- 8. TIPOS DE EMBALAJE

INSERT INTO tipo_embalaje (codigo, nombre) VALUES
('TE001', 'Caja Estándar'),
('TE002', 'Caja Reforzada'),
('TE003', 'Empaque Acolchado'),
('TE004', 'Caja con Espuma de Protección');


-- 9. MODELOS DE LAPTOP

INSERT INTO modelo_laptop (codigo, nombre) VALUES
('ML001', 'ThinkPad T14 Gen 5');


-- 10. MODELOS DE COMPONENTE (ThinkPad T14 Gen 5)

INSERT INTO modelo_componente (codigo, nombre, tipo_componente) VALUES
-- Procesadores
('MC001', 'AMD Ryzen 5 PRO 7540U',           'TC001'),
('MC002', 'AMD Ryzen 7 PRO 7840U',           'TC001'),
('MC003', 'Intel Core Ultra 5 125U',         'TC001'),
('MC004', 'Intel Core Ultra 7 165U',         'TC001'),
-- Memorias RAM
('MC005', 'Samsung 8GB DDR5-5600 SO-DIMM',  'TC002'),
('MC006', 'Samsung 16GB DDR5-5600 SO-DIMM', 'TC002'),
('MC007', 'Micron 32GB DDR5-5600 SO-DIMM',  'TC002'),
-- Almacenamiento SSD
('MC008', 'Samsung PM9A1 256GB NVMe M.2',   'TC003'),
('MC009', 'Samsung PM9A1 512GB NVMe M.2',   'TC003'),
('MC010', 'Samsung PM9A1 1TB NVMe M.2',     'TC003'),
('MC011', 'Seagate FireCuda 2TB NVMe M.2',  'TC003'),
-- Tarjeta Madre
('MC012', 'Lenovo T14 G5 AMD Mainboard',    'TC004'),
('MC013', 'Lenovo T14 G5 Intel Mainboard',  'TC004'),
-- Pantalla
('MC014', 'BOE 14" FHD IPS 400nit',         'TC005'),
('MC015', 'LG 14" WUXGA IPS Touch 400nit',  'TC005'),
('MC016', 'BOE 14" 2.8K OLED 400nit',       'TC005'),
-- Batería
('MC017', 'Lenovo 52.5Wh Li-Ion T14G5',     'TC006'),
-- Teclado
('MC018', 'Lenovo KB T14G5 ES Retroilum.',  'TC007'),
('MC019', 'Lenovo KB T14G5 US Retroilum.',  'TC007'),
-- Touchpad
('MC020', 'Lenovo Touchpad T14G5 NFC',      'TC008'),
('MC021', 'Lenovo Touchpad T14G5 Std',      'TC008'),
-- Cámara Web
('MC022', 'Chicony 1080p FHD IR+RGB',       'TC009'),
('MC023', 'Chicony 5MP IR+RGB',             'TC009'),
-- Tarjeta de Red
('MC024', 'Intel Wi-Fi 6E AX211 M.2',       'TC010'),
('MC025', 'Qualcomm FastConnect 6900 M.2',  'TC010'),
-- Disipador
('MC026', 'Lenovo Thermal Module T14G5 AMD','TC011'),
('MC027', 'Lenovo Thermal Module T14G5 Int','TC011'),
-- Chasis
('MC028', 'Lenovo Top Cover T14G5 Negro',   'TC012'),
('MC029', 'Lenovo Bottom Cover T14G5',      'TC013'),
-- Conector de carga
('MC030', 'Lenovo USB-C Power Connector',   'TC014'),
-- Altavoces
('MC031', 'Harman 2x2W Speaker T14G5',      'TC015');


-- 11. LÍNEAS DE ENSAMBLAJE 
-- 5 normales y una de embalaje

INSERT INTO linea (codigo, nombre, descripcion, estado) VALUES
('LIN001', 'Línea A — Ensamblaje', 'Ensamblaje ThinkPad T14 Gen 5',         'ACTI'),
('LIN002', 'Línea B — Ensamblaje', 'Ensamblaje ThinkPad T14 Gen 5',         'ACTI'),
('LIN003', 'Línea C — Ensamblaje', 'Ensamblaje ThinkPad T14 Gen 5',         'ACTI'),
('LIN004', 'Línea D — Ensamblaje', 'Ensamblaje ThinkPad T14 Gen 5',         'ACTI'),
('LIN005', 'Línea E — Ensamblaje', 'Ensamblaje ThinkPad T14 Gen 5',         'ACTI'),
('LIN006', 'Línea F — Embalaje',   'Proceso de embalaje y empaque final',   'ACTI');


-- 12. ESTACIONES — Líneas de ensamblaje
--
--  EST-X1  Preparación y verificación de componentes
--  EST-X2  Ensamblaje de placa y procesador
--  EST-X3  Integración de pantalla, teclado y chasis
--  EST-X4  Pruebas funcionales y cierre

-- Línea A: Chasis Superior y Periféricos Base
INSERT INTO estacion (codigo, nombre, descripcion, linea) VALUES
('EST-A1', 'A1 — Chasis y Touchpad',    'Inspección del chasis superior e instalación y atornillado del touchpad',                 'LIN001'),
('EST-A2', 'A2 — Módulo de Teclado',    'Colocación del teclado retroiluminado, fijación y ruteo inicial del flexor',              'LIN001'),
('EST-A3', 'A3 — Audio y Conexiones',   'Montaje de altavoces, enrutamiento de cables de audio y fijación acústica',               'LIN001'),
('EST-A4', 'A4 — Conector de Carga',    'Instalación del conector de carga USB-C, anclaje al chasis y revisión de puertos',        'LIN001');

-- Línea B: Tarjeta Madre y Procesamiento
INSERT INTO estacion (codigo, nombre, descripcion, linea) VALUES
('EST-B1', 'B1 — Tarjeta Madre',        'Colocación de la tarjeta madre en el chasis superior y fijación con tornillos',           'LIN002'),
('EST-B2', 'B2 — Conexión de Periféricos','Conexión de los flexores del teclado, touchpad y altavoces a la tarjeta madre',         'LIN002'),
('EST-B3', 'B3 — CPU y Pasta Térmica',  'Montaje del procesador en el socket y aplicación de pasta térmica',                       'LIN002'),
('EST-B4', 'B4 — Memoria RAM',          'Inserción de módulos de memoria RAM en las ranuras SO-DIMM y aseguramiento',              'LIN002');

-- Línea C: Almacenamiento, Red y Refrigeración
INSERT INTO estacion (codigo, nombre, descripcion, linea) VALUES
('EST-C1', 'C1 — Almacenamiento SSD',   'Instalación de la unidad NVMe M.2 y fijación del tornillo de retención',                  'LIN003'),
('EST-C2', 'C2 — Tarjeta de Red',       'Instalación del módulo Wi-Fi y conexión cuidadosa de las antenas de red',                 'LIN003'),
('EST-C3', 'C3 — Disipador Térmico',    'Montaje del módulo térmico sobre el procesador y atornillado en cruz',                    'LIN003'),
('EST-C4', 'C4 — Conexión de Ventilación','Conexión del cable de alimentación del ventilador a la tarjeta madre',                  'LIN003');

-- Línea D: Ensamblaje de Pantalla y Energía
INSERT INTO estacion (codigo, nombre, descripcion, linea) VALUES
('EST-D1', 'D1 — Módulo de Pantalla',   'Preparación de la pantalla e instalación de la cámara web en el marco',                   'LIN004'),
('EST-D2', 'D2 — Bisagras y Enrutamiento','Acoplamiento de las bisagras de pantalla al chasis principal y enrutamiento de cables', 'LIN004'),
('EST-D3', 'D3 — Conexión de Video',    'Conexión del cable de video (eDP) y cable de cámara a la tarjeta madre',                  'LIN004'),
('EST-D4', 'D4 — Batería Principal',    'Colocación de la batería de Li-Ion, atornillado y conexión de alimentación a la placa',   'LIN004');

-- Línea E: Cierre de Equipo y Calidad
INSERT INTO estacion (codigo, nombre, descripcion, linea) VALUES
('EST-E1', 'E1 — Chasis Inferior',      'Colocación de la tapa inferior (Bottom Cover) y atornillado preliminar de las esquinas',  'LIN005'),
('EST-E2', 'E2 — Cierre y Revisión',    'Atornillado final, revisión de ajuste de plásticos y limpieza de excesos',                'LIN005'),
('EST-E3', 'E3 — Pruebas Funcionales',  'Encendido del equipo, pruebas POST, verificación de RAM, SSD, cámara y teclado',          'LIN005'),
('EST-E4', 'E4 — Inspección de Calidad','Validación final por el inspector, registro de aprobación y generación de número de serie','LIN005');

-- Línea F: Embalaje
INSERT INTO estacion (codigo, nombre, descripcion, linea) VALUES
('EST-F1', 'F1 — Limpieza y Escaneo',   'Revisión estética final, limpieza de pantalla, chasis y escaneo del número de serie',     'LIN006'),
('EST-F2', 'F2 — Empaque y Sellado',    'Colocación en caja con material de protección, inclusión de manuales y sellado final',    'LIN006');


-- 13. LOTE DE LAPTOPS

INSERT INTO lote_laptop (codigo, fecha) VALUES
('LOT2026A', '2026-07-15');


-- 14. LOTE DE COMPONENTES (ejemplo)

INSERT INTO lote_comp (codigo, descripcion) VALUES
('LCOMP-001', 'Lote de componentes AMD'),
('LCOMP-002', 'Lote de componentes Intel');



-- 15. EMPLEADOS


-- LINEA A para el equipo matutino
INSERT INTO empleado (numero, nombrePila, primerApell, segundoApell, rol, turno, activo) VALUES
(2607001, 'Carlos',    'García',   'López',    'OPENSA', 'MAT', TRUE),
(2607002, 'María',     'Fernández','Sánchez',  'OPENSA', 'MAT', TRUE),
(2607003, 'Luis',      'Martínez', 'Gómez',    'OPENSA', 'MAT', TRUE),
(2607004, 'Lucía',     'Torres',   'Vargas',   'OPCALI', 'MAT', TRUE),
(2607005, 'Chelly',    'Montes',   'Marcos',   'SUPER',  'MAT', TRUE);


-- LINEA B
INSERT INTO empleado (numero, nombrePila, primerApell, segundoApell, rol, turno, activo) VALUES
(2607006, 'Jorge',     'Ramírez',  'Díaz',     'OPENSA', 'MAT', TRUE),
(2607007, 'Elena',     'Castro',   'Ruiz',     'OPENSA', 'MAT', TRUE),
(2607008, 'Miguel',    'Ortiz',    'Méndez',   'OPENSA', 'MAT', TRUE),
(2607009, 'Roberto',   'Flores',   'Silva',    'OPCALI', 'MAT', TRUE),
(2607010, 'Patricia',  'Navarro',  'Ríos',     'SUPER',  'MAT', TRUE);


-- LINEA C
INSERT INTO empleado (numero, nombrePila, primerApell, segundoApell, rol, turno, activo) VALUES
(2607011, 'Pedro',     'Mendoza',  'Vega',     'OPENSA', 'MAT', TRUE),
(2607012, 'Laura',     'Salinas',  'Ponce',    'OPENSA', 'MAT', TRUE),
(2607013, 'Valeria',   'Guzmán',   'Rojas',    'OPENSA', 'MAT', TRUE),
(2607014, 'Héctor',    'Paz',      'Mora',     'OPCALI', 'MAT', TRUE),
(2607015, 'Diana',     'Ríos',     'Blanco',   'SUPER',  'MAT', TRUE);


-- LINEA D
INSERT INTO empleado (numero, nombrePila, primerApell, segundoApell, rol, turno, activo) VALUES
(2607016, 'Mario',     'Cruz',     'Vidal',    'OPENSA', 'MAT', TRUE),
(2607017, 'Teresa',    'Luna',     'Ortiz',    'OPENSA', 'MAT', TRUE),
(2607018, 'Raúl',      'Navarro',  'Pinto',    'OPENSA', 'MAT', TRUE),
(2607019, 'Carmen',    'Sosa',     'Molina',   'OPCALI', 'MAT', TRUE),
(2607020, 'Gloria',    'Peña',     'Silva',    'SUPER',  'MAT', TRUE);


-- LINEA E
INSERT INTO empleado (numero, nombrePila, primerApell, segundoApell, rol, turno, activo) VALUES
(2607021, 'Hugo',      'Díaz',     'Ramos',    'OPENSA', 'MAT', TRUE),
(2607022, 'Silvia',    'Vargas',   'Luna',     'OPENSA', 'MAT', TRUE),
(2607023, 'Beatriz',   'Méndez',   'Solis',    'OPENSA', 'MAT', TRUE),
(2607024, 'Ramón',     'Blanco',   'Cruz',     'OPCALI', 'MAT', TRUE),
(2607025, 'Julia',     'Cabrera',  'Pérez',    'SUPER',  'MAT', TRUE);


-- LINEA F (EMBALAJE)
INSERT INTO empleado (numero, nombrePila, primerApell, segundoApell, rol, turno, activo) VALUES
(2607026, 'Ricardo',   'Gutiérrez','Pérez',    'OPEMBA', 'MAT', TRUE),
(2607027, 'Isabel',    'Domínguez','Salas',    'OPEMBA', 'MAT', TRUE),
(2607028, 'Arturo',    'Jiménez',  'Cruz',     'SUPER',  'MAT', TRUE);



-- 15.1 ASIGNACION DE UN EMPLEADO A SU LINEA

INSERT INTO empleado_linea (empleado, linea, fecha_inicio, fecha_fin) VALUES
-- LINEA A (LIN001)
(2607001, 'LIN001', '2026-07-15', NULL),
(2607002, 'LIN001', '2026-07-15', NULL),
(2607003, 'LIN001', '2026-07-15', NULL),
(2607004, 'LIN001', '2026-07-15', NULL),
(2607005, 'LIN001', '2026-07-15', NULL);


-- LINEA B (LIN002)
INSERT INTO empleado_linea (empleado, linea, fecha_inicio, fecha_fin) VALUES
(2607006, 'LIN002', '2026-07-15', NULL),
(2607007, 'LIN002', '2026-07-15', NULL),
(2607008, 'LIN002', '2026-07-15', NULL),
(2607009, 'LIN002', '2026-07-15', NULL),
(2607010, 'LIN002', '2026-07-15', NULL);


-- LINEA C (LIN003)
INSERT INTO empleado_linea (empleado, linea, fecha_inicio, fecha_fin) VALUES
(2607011, 'LIN003', '2026-07-15', NULL),
(2607012, 'LIN003', '2026-07-15', NULL),
(2607013, 'LIN003', '2026-07-15', NULL),
(2607014, 'LIN003', '2026-07-15', NULL),
(2607015, 'LIN003', '2026-07-15', NULL);


-- LINEA D (LIN004)
INSERT INTO empleado_linea (empleado, linea, fecha_inicio, fecha_fin) VALUES
(2607016, 'LIN004', '2026-07-15', NULL),
(2607017, 'LIN004', '2026-07-15', NULL),
(2607018, 'LIN004', '2026-07-15', NULL),
(2607019, 'LIN004', '2026-07-15', NULL),
(2607020, 'LIN004', '2026-07-15', NULL);


-- LINEA E (LIN005)
INSERT INTO empleado_linea (empleado, linea, fecha_inicio, fecha_fin) VALUES
(2607021, 'LIN005', '2026-07-15', NULL),
(2607022, 'LIN005', '2026-07-15', NULL),
(2607023, 'LIN005', '2026-07-15', NULL),
(2607024, 'LIN005', '2026-07-15', NULL),
(2607025, 'LIN005', '2026-07-15', NULL);


-- LINEA F - EMBALAJE (LIN006)
INSERT INTO empleado_linea (empleado, linea, fecha_inicio, fecha_fin) VALUES
(2607026, 'LIN006', '2026-07-15', NULL),
(2607027, 'LIN006', '2026-07-15', NULL),
(2607028, 'LIN006', '2026-07-15', NULL);



-- 15.2 ASIGNACION DE UN EMPLEADO A SU ESTACION

INSERT INTO empleado_estacion (empleado, estacion, fecha_inicio, fecha_fin) VALUES
-- LINEA A
(2607001, 'EST-A1', '2026-07-15', NULL),
(2607002, 'EST-A2', '2026-07-15', NULL),
(2607003, 'EST-A3', '2026-07-15', NULL),
(2607004, 'EST-A4', '2026-07-15', NULL);

-- LINEA B
INSERT INTO empleado_estacion (empleado, estacion, fecha_inicio, fecha_fin) VALUES
(2607006, 'EST-B1', '2026-07-15', NULL),
(2607007, 'EST-B2', '2026-07-15', NULL),
(2607008, 'EST-B3', '2026-07-15', NULL),
(2607009, 'EST-B4', '2026-07-15', NULL);

-- LINEA C
INSERT INTO empleado_estacion (empleado, estacion, fecha_inicio, fecha_fin) VALUES
(2607011, 'EST-C1', '2026-07-15', NULL),
(2607012, 'EST-C2', '2026-07-15', NULL),
(2607013, 'EST-C3', '2026-07-15', NULL),
(2607014, 'EST-C4', '2026-07-15', NULL);

-- LINEA D 
INSERT INTO empleado_estacion (empleado, estacion, fecha_inicio, fecha_fin) VALUES
(2607016, 'EST-D1', '2026-07-15', NULL),
(2607017, 'EST-D2', '2026-07-15', NULL),
(2607018, 'EST-D3', '2026-07-15', NULL),
(2607019, 'EST-D4', '2026-07-15', NULL);

-- LINEA E
INSERT INTO empleado_estacion (empleado, estacion, fecha_inicio, fecha_fin) VALUES
(2607021, 'EST-E1', '2026-07-15', NULL),
(2607022, 'EST-E2', '2026-07-15', NULL),
(2607023, 'EST-E3', '2026-07-15', NULL),
(2607024, 'EST-E4', '2026-07-15', NULL);

-- LINEA F (EMBALAJE)
INSERT INTO empleado_estacion (empleado, estacion, fecha_inicio, fecha_fin) VALUES
(2607026, 'EST-F1', '2026-07-15', NULL),
(2607027, 'EST-F2', '2026-07-15', NULL);





INSERT INTO empleado (numero, nombrePila, primerApell, segundoApell,rol,turno, activo)
VALUES (
    2607029, 'Araceli', 'Marcos', 'Montes', 'ADMIN','MAT', TRUE);

INSERT INTO usuario (usuario,contrasena,estado,empleado)
VALUES (
    '0001AMM',
    'pbkdf2_sha256$720000$0o4C7xZGXMGcbTNx1oMeYv$g/MLNK/HQ5E8rtPwUt5JlHHVhMibgYlsMIKse5XHnBs=',
    1,
    2607029
);
