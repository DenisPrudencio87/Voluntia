-- Revisión Alembic 0002. No cambiar retrospectivamente revisión 0001.
SET search_path TO voluntia,public;
CREATE FUNCTION tr_ocupacion_inscripcion() RETURNS trigger LANGUAGE plpgsql SET search_path=voluntia,pg_temp AS $$
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
  IF nuevo NOT IN ('pendiente','espera') OR a.estado<>'publicada' OR now()>=a.fecha_cierre_inscripcion THEN
   RAISE EXCEPTION 'Postulación fuera de plazo o estado' USING ERRCODE='23514'; END IF;
 END IF;
 IF nuevo='aceptada' AND (TG_OP='INSERT' OR anterior<>'aceptada') THEN
  IF a.estado NOT IN ('publicada','cerrada') OR now()>=a.fecha_inicio OR fn_cupos_disponibles(a.id_actividad)<=0 THEN
   RAISE EXCEPTION 'No hay plaza o aceptación fuera de plazo' USING ERRCODE='23514'; END IF;
  IF NOT EXISTS(SELECT 1 FROM organizacion_miembro m JOIN usuario u USING(id_usuario) JOIN organizacion o USING(id_organizacion)
   WHERE m.id_usuario=actor AND m.id_organizacion=a.id_organizacion AND m.estado='activo' AND u.estado='activo'
   AND u.email_verificado AND o.estado_verificacion='verificada') THEN
   RAISE EXCEPTION 'Actor no autorizado a ocupar cupos' USING ERRCODE='42501'; END IF;
  IF NOT EXISTS(SELECT 1 FROM voluntario v JOIN usuario u USING(id_usuario) WHERE v.id_voluntario=NEW.id_voluntario
   AND u.estado='activo' AND u.email_verificado) THEN
   RAISE EXCEPTION 'Participante inactivo o no verificado' USING ERRCODE='23514'; END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER ocupacion_inscripcion BEFORE INSERT OR UPDATE ON inscripcion FOR EACH ROW EXECUTE FUNCTION tr_ocupacion_inscripcion();
CREATE FUNCTION tr_validar_certificado() RETURNS trigger LANGUAGE plpgsql SET search_path=voluntia,pg_temp AS $$
DECLARE a actividad; horas numeric;
BEGIN
 SELECT ac.* INTO a FROM actividad ac JOIN inscripcion i USING(id_actividad) WHERE i.id_inscripcion=NEW.id_inscripcion FOR UPDATE OF ac;
 SELECT round(extract(epoch FROM(s.hora_salida-s.hora_entrada))/3600,2) INTO horas FROM asistencia s
 WHERE s.id_inscripcion=NEW.id_inscripcion AND s.estado='asistio';
 IF a.estado<>'finalizada' OR horas IS NULL OR horas<=0 OR NEW.horas_certificadas<>horas THEN
 RAISE EXCEPTION 'Certificado requiere asistencia y horas coherentes' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER validar_certificado BEFORE INSERT ON certificado FOR EACH ROW EXECUTE FUNCTION tr_validar_certificado();
CREATE TRIGGER certificado_inmutable BEFORE UPDATE OR DELETE ON certificado FOR EACH ROW EXECUTE FUNCTION tr_inmutable();
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA voluntia FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA voluntia FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA voluntia FROM PUBLIC;
DO $$ DECLARE r text; BEGIN
 FOREACH r IN ARRAY ARRAY['anon','authenticated'] LOOP
  IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname=r) THEN
   EXECUTE format('REVOKE ALL ON SCHEMA voluntia FROM %I',r);
   EXECUTE format('REVOKE ALL ON ALL TABLES IN SCHEMA voluntia FROM %I',r);
   EXECUTE format('REVOKE ALL ON ALL SEQUENCES IN SCHEMA voluntia FROM %I',r);
   EXECUTE format('REVOKE ALL ON ALL FUNCTIONS IN SCHEMA voluntia FROM %I',r);
  END IF;
 END LOOP;
END $$;
