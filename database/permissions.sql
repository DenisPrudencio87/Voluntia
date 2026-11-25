-- Ejecutar con propietario/migrador solo después de crear voluntia_runtime.
-- No es una migración automática ni contiene contraseñas.
GRANT USAGE ON SCHEMA voluntia TO voluntia_runtime;
GRANT SELECT,INSERT,UPDATE ON ALL TABLES IN SCHEMA voluntia TO voluntia_runtime;
REVOKE UPDATE ON voluntia.historial_inscripcion,voluntia.bitacora_evento,voluntia.certificado FROM voluntia_runtime;
GRANT DELETE ON voluntia.voluntario_habilidad,voluntia.actividad_habilidad TO voluntia_runtime;
GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA voluntia TO voluntia_runtime;
GRANT EXECUTE ON FUNCTION voluntia.fn_cupos_disponibles(bigint),voluntia.fn_aceptar_inscripcion(bigint,bigint),voluntia.fn_horas_voluntariado(bigint),voluntia.fn_estadisticas_organizacion(bigint) TO voluntia_runtime;
