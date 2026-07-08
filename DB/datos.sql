
INSERT INTO edo_componente (codigo, nombre, descripcion) VALUES
('DISP', 'Disponible', 'Listo para usarse en la línea'),
('ENSAM', 'Ensamblado', 'Ya instalado en una laptop'),
('DEFEC', 'Defectuoso', 'Falla de fábrica, no usable'),
('ASIG', 'Asignado', 'Asignado a una linea de producción'),
('RECH', 'Rechazado', 'Dañado durante el proceso');

INSERT INTO edo_laptop (codigo, nombre) VALUES
('PROC', 'En proceso de ensamblaje'),
('ENSAM', 'Ensamblada'),
('ESP', 'En espera de recolocacion'),
('EMPAC', 'Empacada');

INSERT INTO edo_linea (codigo, nombre, descripcion) VALUES
('ACT', 'Activa', 'Línea operando normalmente'),
('PARO', 'En Paro', 'Línea detenida por incidencia'),
('MANT', 'Mantenimiento', 'Línea en mantenimiento programado'),
('INACT', 'Inactiva', 'Línea sin turno asignado');

INSERT INTO edo_produccion (codigo, nombre) VALUES
('PEND', 'Pendiente'),
('PROCES', 'En Proceso'),
('TERM', 'Terminada'),
('CANC', 'Cancelada');

INSERT INTO tipo_comp (codigo, nombre) VALUES
('CPU', 'Procesador'),
('RAM', 'Memoria RAM'),
('ROM', 'Almacenamiento SSD/HDD'),
('MOBO', 'Tarjeta Madre'),
('BATT', 'Batería'),
('CASE', 'Carcasa'),
('DISP', 'Pantalla');

INSERT INTO tipo_embalaje (codigo, nombre) VALUES
('CAJ_STD', 'Caja Estándar'),
('CAJ_PRE', 'Caja Premium'),
('BULK', 'Tarima / Granel');

INSERT INTO rol (codigo, nombre, descripcion) VALUES
('OP', 'Operador', 'Ensamblador en línea'),
('QA', 'Inspector de Calidad', 'Realiza pruebas y aprueba laptops'),
('SUP', 'Supervisor', 'Encargado de línea y paros'),
('ADMIN', 'Administrador', 'Acceso total al sistema');

INSERT INTO turno (codigo, nombre, hora_entrada, hora_salida) VALUES
('MAT', 'Matutino', '06:00:00', '14:00:00'),
('VESP', 'Vespertino', '14:00:00', '22:00:00'),
('NOCT', 'Nocturno', '22:00:00', '06:00:00');