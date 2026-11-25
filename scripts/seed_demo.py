"""Demo ficticia reproducible. Solo base vacía local/demo; nunca producción."""

import argparse
import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy.engine import make_url
from backend.app.config import settings
from backend.app.db import engine, one, execute, actor_context
from backend.app.security.session import passwords
from backend.app.services.certificates import certificate_pdf
from backend.app.services.storage import put_object


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-remote", action="store_true")
    args = parser.parse_args()
    target = make_url(settings.database_url)
    if settings.app_env not in ("local", "demo"):
        raise SystemExit("Seed demo prohibido fuera de local/demo")
    if target.host not in ("127.0.0.1", "localhost", "db") and not args.allow_remote:
        raise SystemExit(
            "Seed remoto requiere autorización específica y --allow-remote"
        )
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    credentials = {}
    manifest = {}
    with engine.begin() as c:
        if one(c, "SELECT count(*) n FROM usuario")["n"]:
            raise SystemExit(
                "La base ya tiene usuarios. No se modificó ni borró información."
            )
        for label, role in [
            ("admin", "administrador"),
            ("organizacion", "organizacion"),
            ("voluntario", "voluntario"),
        ]:
            password = secrets.token_urlsafe(24)
            email = "demo-" + label + "@example.org"
            u = one(
                c,
                "INSERT INTO usuario(correo,clave_hash,email_verificado) VALUES(:e,:h,true) RETURNING id_usuario",
                e=email,
                h=passwords.hash(password),
            )["id_usuario"]
            execute(
                c,
                "INSERT INTO usuario_rol(id_usuario,id_rol) SELECT :u,id_rol FROM rol WHERE nombre=:r",
                u=u,
                r=role,
            )
            credentials[label] = {"correo": email, "clave": password, "id_usuario": u}
        actor_context(c, credentials["admin"]["id_usuario"])
        volunteer = one(
            c,
            "INSERT INTO voluntario(id_usuario,nombres,apellidos,biografia) VALUES(:u,'Lucía','Ejemplo Ficticio','Perfil ficticio para demostración académica') RETURNING id_voluntario",
            u=credentials["voluntario"]["id_usuario"],
        )["id_voluntario"]
        execute(
            c,
            "INSERT INTO voluntario_habilidad(id_voluntario,id_habilidad,nivel) VALUES(:v,3,'intermedio')",
            v=volunteer,
        )
        organizations = []
        for name, state in [
            ("Manos que Transforman (demo)", "verificada"),
            ("Red Solidaria (demo)", "pendiente"),
        ]:
            o = one(
                c,
                "INSERT INTO organizacion(nombre,descripcion,correo_contacto,estado_verificacion) VALUES(:n,:d,:e,:s) RETURNING id_organizacion",
                n=name,
                d="Organización y documentos ficticios, exclusivamente para la evaluación académica.",
                e="contacto@example.org",
                s=state,
            )["id_organizacion"]
            execute(
                c,
                "INSERT INTO organizacion_miembro(id_organizacion,id_usuario,cargo) VALUES(:o,:u,'administrador')",
                o=o,
                u=credentials["organizacion"]["id_usuario"],
            )
            pdf = certificate_pdf(
                "Documento ficticio",
                "Constancia de demostración",
                name,
                1,
                "NO-ES-IDENTIDAD-REAL",
                now,
            )
            key = put_object(pdf, "documents", o, "pdf", "application/pdf")
            execute(
                c,
                "INSERT INTO documento_organizacion(id_organizacion,tipo_documento,numero_documento,archivo_url,estado_revision) VALUES(:o,:t,:n,:k,:s)",
                o=o,
                t="Constancia ficticia",
                n="DEMO-" + str(o),
                k=key,
                s="aprobado" if state == "verificada" else "pendiente",
            )
            organizations.append(o)
        location = one(
            c,
            "INSERT INTO ubicacion(nombre_lugar,direccion) VALUES('Parque de la comunidad (demo)','Punto de encuentro ficticio, Huancayo') RETURNING id_ubicacion",
        )["id_ubicacion"]
        activities = []
        for idx, title in enumerate(
            [
                "Un parque, muchas nuevas historias",
                "Comparte lo que sabes: tutoría comunitaria",
                "Taller comunitario: aprende y comparte",
            ]
        ):
            begin = now + timedelta(days=3 + idx, hours=2)
            end = begin + timedelta(hours=2)
            a = one(
                c,
                """INSERT INTO actividad(id_organizacion,id_categoria,id_ubicacion,titulo,descripcion,fecha_inicio,fecha_fin,fecha_cierre_inscripcion,cupo_maximo,modalidad,estado,fecha_publicacion)
            VALUES(:o,:cat,:l,:t,:d,:s,:e,:close,:cap,:m,'publicada',now()) RETURNING id_actividad""",
                o=organizations[0],
                cat=1 if idx == 0 else 2,
                l=location if idx == 0 else None,
                t=title,
                d="Actividad ficticia de impacto social. Acompaña a tu comunidad y aporta tus habilidades en un entorno de aprendizaje y colaboración. No se utilizan datos ni documentos reales.",
                s=begin,
                e=end,
                close=begin - timedelta(hours=1),
                cap=12 if idx == 0 else 8,
                m="presencial" if idx == 0 else "virtual",
            )["id_actividad"]
            activities.append(a)
        actor_context(c, credentials["voluntario"]["id_usuario"])
        ins = one(
            c,
            "INSERT INTO inscripcion(id_actividad,id_voluntario,id_estado,motivacion) VALUES(:a,:v,(SELECT id_estado FROM estado_inscripcion WHERE nombre='pendiente'),'Deseo aportar al aprendizaje comunitario de esta demostración.') RETURNING id_inscripcion",
            a=activities[2],
            v=volunteer,
        )["id_inscripcion"]
        actor_context(c, credentials["organizacion"]["id_usuario"])
        execute(
            c,
            "SELECT fn_aceptar_inscripcion(:i,:u)",
            i=ins,
            u=credentials["organizacion"]["id_usuario"],
        )
        # Escenario histórico ficticio provisionado desde consola, sin bypass HTTP.
        begin = now - timedelta(hours=3)
        end = now - timedelta(hours=1)
        execute(
            c,
            "UPDATE actividad SET estado='en_curso',fecha_inicio=:s,fecha_fin=:e,fecha_cierre_inscripcion=:close WHERE id_actividad=:a",
            s=begin,
            e=end,
            close=begin - timedelta(hours=1),
            a=activities[2],
        )
        execute(
            c,
            "INSERT INTO bitacora_evento(id_usuario,accion,entidad,detalle) VALUES(:u,'seed_demo_ficticio','usuario','Cuentas preactivadas ficticias, sin comprobar correo real; escenario histórico académico')",
            u=credentials["admin"]["id_usuario"],
        )
        manifest = {
            "organizacion_verificada": organizations[0],
            "organizacion_pendiente": organizations[1],
            "actividad_historica": activities[2],
            "inscripcion_aceptada": ins,
            "entrada_utc": begin.isoformat(),
            "salida_utc": end.isoformat(),
            "advertencia": "Todo es ficticio; ninguna cuenta demuestra verificación de un correo real.",
        }
    folder = Path(".local")
    folder.mkdir(exist_ok=True)
    (folder / "demo-credentials.json").write_text(
        json.dumps(credentials, indent=2), encoding="utf-8"
    )
    (folder / "demo-manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(
        "Demo ficticia creada. Credenciales privadas en .local/demo-credentials.json, fuera de Git. No compartir cuenta administradora."
    )


if __name__ == "__main__":
    main()
