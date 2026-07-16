-- Active: 1783038914702@@localhost@3306@cuatro

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
TRUNCATE TABLE usuario_token;
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
('ROL001', 'Administrador',       'Acceso total al sistema, gestión de usuarios y configuración general'),
('ROL002', 'Supervisor',          'Supervisión de líneas de ensamblaje, asignación de personal y consulta de reportes'),
('ROL003', 'Operario Ensamblaje', 'Registro de ensamblaje y asociación de componentes en estaciones de trabajo'),
('ROL004', 'Inspector Calidad',   'Registro y consulta de inspecciones de calidad de laptops'),
('ROL005', 'Operario Embalaje',   'Registro del proceso de embalaje y actualización de estado final');


-- 2. TURNOS

INSERT INTO turno (codigo, nombre, hora_entrada, hora_salida) VALUES
('TUR001', 'Matutino',   '06:00:00', '14:00:00'),
('TUR002', 'Vespertino', '14:00:00', '22:00:00');

-- 3. ESTADOS DE LÍNEA

INSERT INTO edo_linea (codigo, nombre, descripcion) VALUES
('EDL001', 'Activa',       'Línea en operación normal'),
('EDL002', 'Inactiva',     'Línea fuera de operación temporalmente'),
('EDL003', 'En Paro',      'Línea detenida por incidencia registrada'),
('EDL004', 'Mantenimiento','Línea en proceso de mantenimiento preventivo o correctivo');


-- 4. ESTADOS DE LAPTOP 

INSERT INTO edo_laptop (codigo, nombre) VALUES
('EDO001', 'Registrada'),       
('EDO002', 'En Ensamblaje'),    
('EDO003', 'En Inspección'),    
('EDO004', 'Aprobada'),         
('EDO005', 'Rechazada'),        
('EDO006', 'Pendiente Embalaje'),
('EDO007', 'Embalada');         


-- 5. ESTADOS DE PRODUCCIÓN 

INSERT INTO edo_produccion (codigo, nombre) VALUES
('EDP001', 'Pendiente'),
('EDP002', 'En Proceso'),
('EDP003', 'Completada'),
('EDP004', 'Cancelada');


-- 6. TIPOS DE COMPONENTE

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


-- 7. TIPOS DE EMBALAJE

INSERT INTO tipo_embalaje (codigo, nombre) VALUES
('TE001', 'Caja Estándar'),
('TE002', 'Caja Reforzada'),
('TE003', 'Empaque Acolchado'),
('TE004', 'Caja con Espuma de Protección');


-- 8. MODELOS DE LAPTOP

INSERT INTO modelo_laptop (codigo, nombre) VALUES
('ML001', 'ThinkPad T14 Gen 5');


-- 9. MODELOS DE COMPONENTE (ThinkPad T14 Gen 5)

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


-- 10. LÍNEAS DE ENSAMBLAJE 
-- 5 normales y una de embalaje

INSERT INTO linea (codigo, nombre, descripcion, estado) VALUES
('LIN001', 'Línea A — Ensamblaje', 'Ensamblaje ThinkPad T14 Gen 5',         'EDL001'),
('LIN002', 'Línea B — Ensamblaje', 'Ensamblaje ThinkPad T14 Gen 5',         'EDL001'),
('LIN003', 'Línea C — Ensamblaje', 'Ensamblaje ThinkPad T14 Gen 5',         'EDL001'),
('LIN004', 'Línea D — Ensamblaje', 'Ensamblaje ThinkPad T14 Gen 5',         'EDL001'),
('LIN005', 'Línea E — Ensamblaje', 'Ensamblaje ThinkPad T14 Gen 5',         'EDL001'),
('LIN006', 'Línea F — Embalaje',   'Proceso de embalaje y empaque final',   'EDL001');


-- 11. ESTACIONES — Líneas de ensamblaje
--
--  EST-X1  Preparación y verificación de componentes
--  EST-X2  Ensamblaje de placa y procesador
--  EST-X3  Integración de pantalla, teclado y chasis
--  EST-X4  Pruebas funcionales y cierre


-- Línea A
INSERT INTO estacion (codigo, nombre, descripcion, linea) VALUES
('EST-A1', 'A1 — Preparación',          'Verificación y preparación de componentes antes del ensamblaje', 'LIN001'),
('EST-A2', 'A2 — Placa y CPU',          'Instalación de tarjeta madre, procesador, RAM y SSD',            'LIN001'),
('EST-A3', 'A3 — Chasis y Periféricos', 'Integración de pantalla, teclado, touchpad y chasis',            'LIN001'),
('EST-A4', 'A4 — Pruebas y Cierre',     'Pruebas funcionales POST, cierre de ensamblaje y etiquetado',    'LIN001');

-- Línea B
INSERT INTO estacion (codigo, nombre, descripcion, linea) VALUES
('EST-B1', 'B1 — Preparación',          'Verificación y preparación de componentes antes del ensamblaje', 'LIN002'),
('EST-B2', 'B2 — Placa y CPU',          'Instalación de tarjeta madre, procesador, RAM y SSD',            'LIN002'),
('EST-B3', 'B3 — Chasis y Periféricos', 'Integración de pantalla, teclado, touchpad y chasis',            'LIN002'),
('EST-B4', 'B4 — Pruebas y Cierre',     'Pruebas funcionales POST, cierre de ensamblaje y etiquetado',    'LIN002');

-- Línea C
INSERT INTO estacion (codigo, nombre, descripcion, linea) VALUES
('EST-C1', 'C1 — Preparación',          'Verificación y preparación de componentes antes del ensamblaje', 'LIN003'),
('EST-C2', 'C2 — Placa y CPU',          'Instalación de tarjeta madre, procesador, RAM y SSD',            'LIN003'),
('EST-C3', 'C3 — Chasis y Periféricos', 'Integración de pantalla, teclado, touchpad y chasis',            'LIN003'),
('EST-C4', 'C4 — Pruebas y Cierre',     'Pruebas funcionales POST, cierre de ensamblaje y etiquetado',    'LIN003');

-- Línea D
INSERT INTO estacion (codigo, nombre, descripcion, linea) VALUES
('EST-D1', 'D1 — Preparación',          'Verificación y preparación de componentes antes del ensamblaje', 'LIN004'),
('EST-D2', 'D2 — Placa y CPU',          'Instalación de tarjeta madre, procesador, RAM y SSD',            'LIN004'),
('EST-D3', 'D3 — Chasis y Periféricos', 'Integración de pantalla, teclado, touchpad y chasis',            'LIN004'),
('EST-D4', 'D4 — Pruebas y Cierre',     'Pruebas funcionales POST, cierre de ensamblaje y etiquetado',    'LIN004');

-- Línea E
INSERT INTO estacion (codigo, nombre, descripcion, linea) VALUES
('EST-E1', 'E1 — Preparación',          'Verificación y preparación de componentes antes del ensamblaje', 'LIN005'),
('EST-E2', 'E2 — Placa y CPU',          'Instalación de tarjeta madre, procesador, RAM y SSD',            'LIN005'),
('EST-E3', 'E3 — Chasis y Periféricos', 'Integración de pantalla, teclado, touchpad y chasis',            'LIN005'),
('EST-E4', 'E4 — Pruebas y Cierre',     'Pruebas funcionales POST, cierre de ensamblaje y etiquetado',    'LIN005');

-- Línea F — Embalaje
INSERT INTO estacion (codigo, nombre, descripcion, linea) VALUES
('EST-F1', 'F1 — Verificación Pre-Embalaje', 'Revisión final de número de serie, estado y etiquetado antes del empaque',    'LIN006'),
('EST-F2', 'F2 — Empaque y Sellado',         'Selección de tipo de embalaje, empaque físico y sellado final del producto',  'LIN006');


-- 12. LOTE DE LAPTOPS

INSERT INTO lote_laptop (codigo, fecha) VALUES
('LOT2026A', '2026-07-15');


-- 13. LOTE DE COMPONENTES (ejemplo)

INSERT INTO lote_comp (codigo, descripcion) VALUES
('LCOMP-001', 'Lote de componentes AMD'),
('LCOMP-002', 'Lote de componentes Intel');
