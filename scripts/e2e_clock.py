"""Reloj de fixture exclusivo de E2E. Nunca importado por la aplicación."""
import json
import os
import sys
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
url=os.environ['TEST_DATABASE_URL']
target=make_url(url)
if not target.database.endswith('_test') or target.host not in ('localhost','127.0.0.1','postgres'):
    raise RuntimeError('Reloj E2E limitado a base local *_test')
activity=int(sys.argv[1])
with create_engine(url,connect_args={'options':'-csearch_path=voluntia,public'}).begin() as c:
    if '--read' not in sys.argv:
        c.execute(text("UPDATE actividad SET fecha_inicio=date_trunc('minute',now()-interval '3 hours'),fecha_fin=date_trunc('minute',now()-interval '1 hour'),fecha_cierre_inscripcion=date_trunc('minute',now()-interval '4 hours') WHERE id_actividad=:a"),{'a':activity})
    row=c.execute(text('SELECT fecha_inicio,fecha_fin FROM actividad WHERE id_actividad=:a'),{'a':activity}).one()
    print(json.dumps({'start':row[0].isoformat(),'end':row[1].isoformat()}))
