SET search_path TO voluntia, public;
CREATE FUNCTION fn_cupos_disponibles(p_actividad bigint) RETURNS integer
LANGUAGE sql STABLE SET search_path=voluntia,pg_temp AS $$
 SELECT a.cupo_maximo - (SELECT count(*)::int FROM inscripcion i JOIN estado_inscripcion e USING(id_estado)
 WHERE i.id_actividad=a.id_actividad AND e.nombre IN ('aceptada','finalizada'))
 FROM actividad a WHERE a.id_actividad=p_actividad;
$$;
CREATE FUNCTION fn_horas_voluntariado(p_voluntario bigint) RETURNS numeric
LANGUAGE sql STABLE SET search_path=voluntia,pg_temp AS $$
 SELECT coalesce(sum(extract(epoch FROM (a.hora_salida-a.hora_entrada))/3600),0)
 FROM asistencia a JOIN inscripcion i USING(id_inscripcion)
 WHERE i.id_voluntario=p_voluntario AND a.estado='asistio';
$$;
CREATE FUNCTION fn_estadisticas_organizacion(p_organizacion bigint)
RETURNS TABLE(actividades bigint,inscritos bigint,asistencias bigint,horas numeric,beneficiarios bigint)
LANGUAGE sql STABLE SET search_path=voluntia,pg_temp AS $$
 SELECT
 (SELECT count(*) FROM actividad WHERE id_organizacion=p_organizacion),
 (SELECT count(*) FROM inscripcion i JOIN actividad a USING(id_actividad) WHERE a.id_organizacion=p_organizacion),
 (SELECT count(*) FROM asistencia s JOIN inscripcion i USING(id_inscripcion) JOIN actividad a USING(id_actividad)
  WHERE a.id_organizacion=p_organizacion AND s.estado='asistio'),
 (SELECT coalesce(sum(extract(epoch FROM(s.hora_salida-s.hora_entrada))/3600),0)
  FROM asistencia s JOIN inscripcion i USING(id_inscripcion) JOIN actividad a USING(id_actividad)
  WHERE a.id_organizacion=p_organizacion AND s.estado='asistio'),
 (SELECT coalesce(sum(ia.beneficiarios_estimados),0) FROM impacto_actividad ia JOIN actividad a USING(id_actividad)
  WHERE a.id_organizacion=p_organizacion);
$$;
CREATE FUNCTION fn_aceptar_inscripcion(p_inscripcion bigint,p_actor bigint) RETURNS void
LANGUAGE plpgsql SET search_path=voluntia,pg_temp AS $$
DECLARE a actividad; i inscripcion; estado_actual text;
BEGIN
 IF nullif(current_setting('app.actor_id',true),'')::bigint IS DISTINCT FROM p_actor THEN
  RAISE EXCEPTION 'Actor inválido' USING ERRCODE='42501'; END IF;
 SELECT ac.* INTO a FROM actividad ac JOIN inscripcion ins USING(id_actividad)
 WHERE ins.id_inscripcion=p_inscripcion FOR UPDATE OF ac;
 IF NOT FOUND THEN RAISE EXCEPTION 'Inscripción inexistente' USING ERRCODE='P0002'; END IF;
 SELECT * INTO i FROM inscripcion WHERE id_inscripcion=p_inscripcion FOR UPDATE;
 SELECT nombre INTO estado_actual FROM estado_inscripcion WHERE id_estado=i.id_estado;
 IF NOT EXISTS(SELECT 1 FROM organizacion_miembro m JOIN usuario u USING(id_usuario)
 JOIN organizacion o USING(id_organizacion) WHERE m.id_organizacion=a.id_organizacion
 AND m.id_usuario=p_actor AND m.estado='activo' AND u.estado='activo' AND u.email_verificado
 AND o.estado_verificacion='verificada') THEN
 RAISE EXCEPTION 'Miembro no autorizado' USING ERRCODE='42501'; END IF;
 IF estado_actual NOT IN ('pendiente','espera') OR a.estado NOT IN ('publicada','cerrada') OR now() >= a.fecha_inicio THEN
 RAISE EXCEPTION 'No admite aceptación' USING ERRCODE='23514'; END IF;
 IF fn_cupos_disponibles(a.id_actividad) <= 0 THEN RAISE EXCEPTION 'Sin cupos disponibles' USING ERRCODE='23514'; END IF;
 UPDATE inscripcion SET id_estado=(SELECT id_estado FROM estado_inscripcion WHERE nombre='aceptada'),
 fecha_actualizacion=now() WHERE id_inscripcion=p_inscripcion;
 -- El trigger produce historial, bitácora y aviso exactamente una vez.
END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA voluntia FROM PUBLIC;
