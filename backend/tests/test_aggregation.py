from backend.app.db import one, execute, actor_context


def test_hours_statistics_not_multiplied_by_evidence(db_engine, scenario):
    with db_engine.begin() as c:
        actor_context(c, scenario["actor"])
        ins = scenario["inscripciones"][0]
        execute(c, "SELECT fn_aceptar_inscripcion(:i,:u)", i=ins, u=scenario["actor"])
        execute(
            c,
            "UPDATE actividad SET fecha_inicio=now()-interval '3 hours',fecha_fin=now()-interval '1 hour',fecha_cierre_inscripcion=now()-interval '4 hours' WHERE id_actividad=:a",
            a=scenario["actividad"],
        )
        execute(
            c,
            "INSERT INTO asistencia(id_inscripcion,estado,hora_entrada,hora_salida) SELECT :i,'asistio',fecha_inicio,fecha_fin FROM actividad WHERE id_actividad=:a",
            i=ins,
            a=scenario["actividad"],
        )
        execute(
            c,
            "INSERT INTO impacto_actividad(id_actividad,beneficiarios_estimados,horas_voluntariado,descripcion_impacto) VALUES(:a,13,2,'Resultado ficticio')",
            a=scenario["actividad"],
        )
        for _ in range(2):
            execute(
                c,
                "INSERT INTO evidencia_actividad(id_actividad,id_usuario,tipo,archivo_url,descripcion) VALUES(:a,:u,'imagen','ficticio','Evidencia de prueba')",
                a=scenario["actividad"],
                u=scenario["actor"],
            )
        stats = one(
            c, "SELECT * FROM fn_estadisticas_organizacion(:o)", o=scenario["org"]
        )
        assert (
            stats["inscritos"] == 3
            and stats["asistencias"] == 1
            and stats["horas"] == 2
            and stats["beneficiarios"] == 13
        )
        assert one(c, "SELECT fn_horas_voluntariado(1) n")["n"] == 2
