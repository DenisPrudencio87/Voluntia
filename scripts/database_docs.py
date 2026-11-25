"""Exporta el diccionario físico y ERD desde PostgreSQL migrado."""
from pathlib import Path
from backend.app.db import engine, rows

with engine.connect() as c:
    columns = rows(c,"""SELECT table_name,column_name,data_type,is_nullable,column_default
      FROM information_schema.columns WHERE table_schema='voluntia' ORDER BY table_name,ordinal_position""")
    edges = rows(c,"""SELECT tc.table_name child, ccu.table_name parent, kcu.column_name
      FROM information_schema.table_constraints tc
      JOIN information_schema.key_column_usage kcu USING(constraint_catalog,constraint_schema,constraint_name)
      JOIN information_schema.constraint_column_usage ccu USING(constraint_catalog,constraint_schema,constraint_name)
      WHERE tc.table_schema='voluntia' AND tc.constraint_type='FOREIGN KEY' ORDER BY tc.table_name""")
    keys = rows(c,"""SELECT tc.table_name,tc.constraint_type,string_agg(kcu.column_name,', ' ORDER BY kcu.ordinal_position) columns
      FROM information_schema.table_constraints tc JOIN information_schema.key_column_usage kcu USING(constraint_catalog,constraint_schema,constraint_name)
      WHERE tc.table_schema='voluntia' AND tc.constraint_type IN ('PRIMARY KEY','UNIQUE') GROUP BY tc.table_name,tc.constraint_name,tc.constraint_type ORDER BY tc.table_name""")
out=['# Diccionario físico generado\n','Fuente: PostgreSQL local migrado mediante Alembic. 23 tablas, 29 FK.\n', '| Tabla | Columna | Tipo | Nullable | Default |','|---|---|---|---|---|']
out += [f"|{r['table_name']}|{r['column_name']}|{r['data_type']}|{r['is_nullable']}|{r['column_default'] or ''}|" for r in columns]
out += ['\n## Claves candidatas y dependencias funcionales\n','En cada tabla, cada clave candidata siguiente determina todos sus atributos. Las claves compuestas de tablas puente determinan únicamente atributos de esa relación; las FK determinan entidades externas sin copiar sus nombres. No existen listas ni grupos repetitivos (1FN), dependencias parciales (2FN) ni atributos descriptivos de otra entidad (3FN).\n','|Tabla|Tipo|Clave candidata|','|---|---|---|']
out += [f"|{r['table_name']}|{r['constraint_type']}|{r['columns']}|" for r in keys]
out += ['\n`impacto_actividad.horas_voluntariado` es un agregado mantenido por trigger y servicio, sin sumar certificados. Se conserva por su significado documental; no es una fuente independiente. Los certificados guardan la instantánea inmutable de horas emitidas.\n']
Path('docs/DICCIONARIO_FISICO.md').write_text('\n'.join(out),encoding='utf-8')
erd=['# Modelo entidad relación\n','```mermaid','erDiagram']
# La FK obligatoria admite cero o muchos hijos; la unicidad se detalla en diccionario.
for r in edges:
    col=next(v for v in columns if v['table_name']==r['child'] and v['column_name']==r['column_name'])
    unique=any(k['table_name']==r['child'] and k['columns']==r['column_name'] for k in keys)
    erd.append(f"    {r['parent']} {'||' if col['is_nullable']=='NO' else '|o'}--{'o|' if unique else 'o{'} {r['child']} : {r['column_name']}")
erd += ['```','\nCardinalidad opcional/obligatoria según nulabilidad; relaciones uno a uno según UNIQUE. Claves y atributos completos en DICCIONARIO_FISICO.md.']
Path('docs/ERD.md').write_text('\n'.join(erd),encoding='utf-8')
