from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from sqlalchemy.exc import DBAPIError, IntegrityError
from backend.app.db import one, execute, actor_context


def test_23_tables_and_constraints(db_engine):
    with db_engine.connect() as c:
        assert one(c,"SELECT count(*) n FROM information_schema.tables WHERE table_schema='voluntia'")['n']==23
        assert one(c,"SELECT count(*) n FROM information_schema.table_constraints WHERE table_schema='voluntia' AND constraint_type='FOREIGN KEY'")['n'] == 29


def test_email_uniqueness_and_normalization(db_engine):
    with db_engine.begin() as c:
        execute(c,"INSERT INTO usuario(correo,clave_hash) VALUES('persona@example.org','hash')")
    for correo in ('persona@example.org','PERSONA@example.org'):
        with pytest.raises(IntegrityError), db_engine.begin() as c:
            execute(c,"INSERT INTO usuario(correo,clave_hash) VALUES(:correo,'hash')",correo=correo)


def test_last_place_concurrent(db_engine,scenario):
    barrier=Barrier(2)
    def accept(ins):
        try:
            with db_engine.begin() as c:
                actor_context(c,scenario['actor'])
                barrier.wait(timeout=10)
                execute(c,'SELECT fn_aceptar_inscripcion(:i,:u)',i=ins,u=scenario['actor'])
            return 'aceptada'
        except IntegrityError:
            return 'conflicto'
    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(accept,scenario['inscripciones'][:2]))==['aceptada','conflicto']
    with db_engine.connect() as c:
        assert one(c,'SELECT fn_cupos_disponibles(:a) n',a=scenario['actividad'])['n']==0
        assert one(c,'SELECT count(*) n FROM historial_inscripcion')['n']==4
        assert one(c,'SELECT count(*) n FROM notificacion')['n']==4


def test_acceptance_rollback(db_engine,scenario):
    with pytest.raises(RuntimeError), db_engine.begin() as c:
        actor_context(c,scenario['actor'])
        execute(c,'SELECT fn_aceptar_inscripcion(:i,:u)',i=scenario['inscripciones'][0],u=scenario['actor'])
        raise RuntimeError('Fallo posterior, debe revertir todos los efectos')
    with db_engine.connect() as c:
        assert one(c,'SELECT fn_cupos_disponibles(:a) n',a=scenario['actividad'])['n']==1
        assert one(c,'SELECT count(*) n FROM historial_inscripcion')['n']==3
        assert one(c,'SELECT count(*) n FROM notificacion')['n']==3


def test_actor_required_and_history_immutable(db_engine,scenario):
    with pytest.raises(DBAPIError), db_engine.begin() as c:
        execute(c,'SELECT fn_aceptar_inscripcion(:i,:u)',i=scenario['inscripciones'][0],u=scenario['actor'])
    with pytest.raises(DBAPIError), db_engine.begin() as c:
        execute(c,"UPDATE historial_inscripcion SET comentario='Alteración'")


def test_invalid_capacity_and_dates(db_engine,scenario):
    with db_engine.begin() as c:
        actor_context(c,scenario['actor'])
        execute(c,'SELECT fn_aceptar_inscripcion(:i,:u)',i=scenario['inscripciones'][0],u=scenario['actor'])
    for statement in ('UPDATE actividad SET cupo_maximo=0','UPDATE actividad SET fecha_fin=fecha_inicio'):
        with pytest.raises(IntegrityError), db_engine.begin() as c:
            execute(c,statement)


def test_duplicate_application_concurrent(db_engine,scenario):
    # La restricción UNIQUE protege incluso ante escritores con conexiones distintas.
    with pytest.raises(IntegrityError), db_engine.begin() as c:
        actor_context(c,scenario['usuarios'][1])
        execute(c,"INSERT INTO inscripcion(id_actividad,id_voluntario,id_estado,motivacion) SELECT id_actividad,id_voluntario,id_estado,'Otra' FROM inscripcion LIMIT 1")


def test_aggregation_separate_joins(db_engine,scenario):
    with db_engine.connect() as c:
        stats=one(c,'SELECT * FROM fn_estadisticas_organizacion(:o)',o=scenario['org'])
        assert stats['actividades']==1 and stats['inscritos']==3 and stats['horas']==0
