SET search_path TO voluntia, public;
SELECT id_actividad,titulo,fecha_inicio,fn_cupos_disponibles(id_actividad) AS cupos FROM actividad WHERE estado='publicada';
SELECT o.nombre,count(a.id_actividad) actividades FROM organizacion o LEFT JOIN actividad a USING(id_organizacion) GROUP BY o.id_organizacion;
SELECT * FROM fn_estadisticas_organizacion(1);
SELECT fn_horas_voluntariado(1);
SELECT i.id_inscripcion,e.nombre,h.fecha_cambio FROM inscripcion i JOIN historial_inscripcion h USING(id_inscripcion) JOIN estado_inscripcion e ON e.id_estado=h.id_estado ORDER BY h.fecha_cambio;
-- Aceptación: actor obtenido de una sesión validada por backend, no del cliente.
-- BEGIN; SELECT set_config('app.actor_id','ID_PRIVADO',true);
-- SELECT fn_aceptar_inscripcion(ID_INSCRIPCION,ID_PRIVADO); COMMIT;
