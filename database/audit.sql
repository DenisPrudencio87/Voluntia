-- Revisión 0003: conservar 23 tablas y no modificar revisiones publicadas.
SET search_path TO voluntia,public;
CREATE OR REPLACE FUNCTION fn_aceptar_inscripcion(p_inscripcion bigint,p_actor bigint) RETURNS void
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
 JOIN organizacion o USING(id_organizacion) JOIN usuario_rol ur USING(id_usuario) JOIN rol r USING(id_rol)
 WHERE m.id_organizacion=a.id_organizacion AND m.id_usuario=p_actor AND m.estado='activo'
 AND u.estado='activo' AND u.email_verificado AND o.estado_verificacion='verificada'
 AND ur.activo AND r.nombre='organizacion') THEN
 RAISE EXCEPTION 'Miembro no autorizado' USING ERRCODE='42501'; END IF;
 IF estado_actual NOT IN ('pendiente','espera') OR a.estado NOT IN ('publicada','cerrada') OR clock_timestamp() >= a.fecha_inicio THEN
 RAISE EXCEPTION 'No admite aceptación' USING ERRCODE='23514'; END IF;
 IF fn_cupos_disponibles(a.id_actividad) <= 0 THEN RAISE EXCEPTION 'Sin cupos disponibles' USING ERRCODE='23514'; END IF;
 UPDATE inscripcion SET id_estado=(SELECT id_estado FROM estado_inscripcion WHERE nombre='aceptada'),
 fecha_actualizacion=clock_timestamp() WHERE id_inscripcion=p_inscripcion;
END $$;
CREATE OR REPLACE FUNCTION tr_ocupacion_inscripcion() RETURNS trigger LANGUAGE plpgsql SET search_path=voluntia,pg_temp AS $$
DECLARE a actividad; nuevo text; anterior text; actor bigint;
BEGIN
 SELECT * INTO a FROM actividad WHERE id_actividad=NEW.id_actividad FOR UPDATE;
 SELECT nombre INTO nuevo FROM estado_inscripcion WHERE id_estado=NEW.id_estado;
 actor:=nullif(current_setting('app.actor_id',true),'')::bigint;
 IF TG_OP='UPDATE' THEN
  IF NEW.id_actividad<>OLD.id_actividad OR NEW.id_voluntario<>OLD.id_voluntario THEN
   RAISE EXCEPTION 'No se cambia el titular de una inscripción' USING ERRCODE='23514'; END IF;
  SELECT nombre INTO anterior FROM estado_inscripcion WHERE id_estado=OLD.id_estado;
 ELSE
  IF nuevo NOT IN ('pendiente','espera') OR a.estado<>'publicada' OR clock_timestamp()>=a.fecha_cierre_inscripcion THEN
   RAISE EXCEPTION 'Postulación fuera de plazo o estado' USING ERRCODE='23514'; END IF;
 END IF;
 IF nuevo='aceptada' AND (TG_OP='INSERT' OR anterior<>'aceptada') THEN
  IF a.estado NOT IN ('publicada','cerrada') OR clock_timestamp()>=a.fecha_inicio OR fn_cupos_disponibles(a.id_actividad)<=0 THEN
   RAISE EXCEPTION 'No hay plaza o aceptación fuera de plazo' USING ERRCODE='23514'; END IF;
  IF NOT EXISTS(SELECT 1 FROM organizacion_miembro m JOIN usuario u USING(id_usuario) JOIN organizacion o USING(id_organizacion)
   JOIN usuario_rol ur USING(id_usuario) JOIN rol r USING(id_rol)
   WHERE m.id_usuario=actor AND m.id_organizacion=a.id_organizacion AND m.estado='activo' AND u.estado='activo'
   AND u.email_verificado AND o.estado_verificacion='verificada' AND ur.activo AND r.nombre='organizacion') THEN
   RAISE EXCEPTION 'Actor no autorizado a ocupar cupos' USING ERRCODE='42501'; END IF;
  IF NOT EXISTS(SELECT 1 FROM voluntario v JOIN usuario u USING(id_usuario)
   JOIN usuario_rol ur USING(id_usuario) JOIN rol r USING(id_rol) WHERE v.id_voluntario=NEW.id_voluntario
   AND u.estado='activo' AND u.email_verificado AND ur.activo AND r.nombre='voluntario') THEN
   RAISE EXCEPTION 'Participante inactivo o sin rol voluntario' USING ERRCODE='23514'; END IF;
 END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION fn_aceptar_inscripcion(bigint,bigint),tr_ocupacion_inscripcion() FROM PUBLIC;
