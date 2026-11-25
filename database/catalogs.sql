SET search_path TO voluntia, public;
INSERT INTO rol(nombre,descripcion) VALUES ('administrador','Supervisión general'),('voluntario','Participación social'),('organizacion','Gestión mediante membresía');
INSERT INTO estado_inscripcion(nombre) VALUES ('pendiente'),('aceptada'),('rechazada'),('cancelada'),('espera'),('finalizada');
INSERT INTO categoria(nombre,icono) VALUES ('Medio ambiente','tree'),('Educación','book'),('Salud','heart-pulse'),('Bienestar animal','paw'),('Ayuda humanitaria','people'),('Adultos mayores','person-heart'),('Inclusión social','globe');
INSERT INTO habilidad(nombre) VALUES ('Primeros auxilios'),('Enseñanza'),('Logística'),('Fotografía'),('Programación'),('Cocina'),('Idiomas');
