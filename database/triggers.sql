SET search_path TO voluntia, public;
CREATE FUNCTION tr_historial_inscripcion() RETURNS trigger LANGUAGE plpgsql SET search_path=voluntia,pg_temp AS $$
DECLARE actor bigint; nuevo text; anterior text;
BEGIN
 actor := nullif(current_setting('app.actor_id',true),'')::bigint;
 IF actor IS NULL OR NOT EXISTS(SELECT 1 FROM usuario WHERE id_usuario=actor AND estado='activo') THEN
 RAISE EXCEPTION 'Falta actor transaccional activo' USING ERRCODE='42501'; END IF;
 IF TG_OP='UPDATE' AND NEW.id_estado=OLD.id_estado THEN RETURN NEW; END IF;
 SELECT nombre INTO nuevo FROM estado_inscripcion WHERE id_estado=NEW.id_estado;
 IF TG_OP='UPDATE' THEN
  SELECT nombre INTO anterior FROM estado_inscripcion WHERE id_estado=OLD.id_estado;
  IF NOT ((anterior IN ('pendiente','espera') AND nuevo IN ('aceptada','rechazada','cancelada'))
   OR (anterior='pendiente' AND nuevo='espera') OR (anterior='aceptada' AND nuevo IN ('cancelada','finalizada'))) THEN
   RAISE EXCEPTION 'Transición inválida' USING ERRCODE='23514'; END IF;
 END IF;
 INSERT INTO historial_inscripcion(id_inscripcion,id_estado,id_usuario_responsable,comentario)
 VALUES(NEW.id_inscripcion,NEW.id_estado,actor,NEW.observacion);
 INSERT INTO bitacora_evento(id_usuario,accion,entidad,id_registro,detalle)
 VALUES(actor,'estado_inscripcion','inscripcion',NEW.id_inscripcion,nuevo);
 INSERT INTO notificacion(id_usuario,titulo,mensaje,tipo,url_destino)
 SELECT id_usuario,'Participación actualizada','Estado: '||nuevo,'inscripcion','/panel/voluntario'
 FROM voluntario WHERE id_voluntario=NEW.id_voluntario;
 RETURN NEW;
END $$;
CREATE TRIGGER historial_inscripcion AFTER INSERT OR UPDATE ON inscripcion FOR EACH ROW EXECUTE FUNCTION tr_historial_inscripcion();
CREATE FUNCTION tr_inmutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Registro inmutable' USING ERRCODE='42501'; END $$;
CREATE TRIGGER historial_inmutable BEFORE UPDATE OR DELETE ON historial_inscripcion FOR EACH ROW EXECUTE FUNCTION tr_inmutable();
CREATE TRIGGER bitacora_inmutable BEFORE UPDATE OR DELETE ON bitacora_evento FOR EACH ROW EXECUTE FUNCTION tr_inmutable();
CREATE FUNCTION tr_validar_cupo() RETURNS trigger LANGUAGE plpgsql SET search_path=voluntia,pg_temp AS $$
BEGIN
 IF NEW.cupo_maximo < (SELECT count(*) FROM inscripcion i JOIN estado_inscripcion e USING(id_estado)
 WHERE i.id_actividad=NEW.id_actividad AND e.nombre IN ('aceptada','finalizada')) THEN
 RAISE EXCEPTION 'Cupo inferior a participantes confirmados' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER validar_cupo BEFORE UPDATE OF cupo_maximo ON actividad FOR EACH ROW EXECUTE FUNCTION tr_validar_cupo();
CREATE FUNCTION tr_validar_asistencia() RETURNS trigger LANGUAGE plpgsql SET search_path=voluntia,pg_temp AS $$
DECLARE a actividad; estado_ins text;
BEGIN
 SELECT ac.* INTO a FROM actividad ac JOIN inscripcion i USING(id_actividad) WHERE i.id_inscripcion=NEW.id_inscripcion FOR UPDATE OF ac;
 SELECT e.nombre INTO estado_ins FROM inscripcion i JOIN estado_inscripcion e USING(id_estado) WHERE i.id_inscripcion=NEW.id_inscripcion;
 IF EXISTS(SELECT 1 FROM certificado WHERE id_inscripcion=NEW.id_inscripcion) OR estado_ins NOT IN ('aceptada','finalizada')
 OR a.estado='cancelada' OR now()<a.fecha_inicio OR NEW.hora_entrada<a.fecha_inicio OR NEW.hora_salida>a.fecha_fin THEN
 RAISE EXCEPTION 'Asistencia inválida o certificada' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER validar_asistencia BEFORE INSERT OR UPDATE ON asistencia FOR EACH ROW EXECUTE FUNCTION tr_validar_asistencia();
CREATE FUNCTION tr_sincronizar_impacto() RETURNS trigger LANGUAGE plpgsql SET search_path=voluntia,pg_temp AS $$
BEGIN
 UPDATE impacto_actividad SET horas_voluntariado=(SELECT coalesce(sum(extract(epoch FROM(s.hora_salida-s.hora_entrada))/3600),0)
 FROM asistencia s JOIN inscripcion i USING(id_inscripcion) WHERE i.id_actividad=impacto_actividad.id_actividad AND s.estado='asistio')
 WHERE id_actividad=(SELECT id_actividad FROM inscripcion WHERE id_inscripcion=NEW.id_inscripcion);
 RETURN NEW;
END $$;
CREATE TRIGGER sincronizar_impacto AFTER INSERT OR UPDATE ON asistencia FOR EACH ROW EXECUTE FUNCTION tr_sincronizar_impacto();
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA voluntia FROM PUBLIC;
