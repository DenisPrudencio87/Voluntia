"""Fija dependencias instaladas, incluyendo extras, sin rutas locales."""
from importlib.metadata import distribution
from pathlib import Path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


def lock(roots):
    found, pending = {}, [(Requirement(r), set(Requirement(r).extras)) for r in roots]
    visited = set()
    while pending:
        req, extras = pending.pop()
        key = (canonicalize_name(req.name), tuple(sorted(extras)))
        if key in visited:
            continue
        visited.add(key)
        dist = distribution(req.name)
        found[canonicalize_name(dist.metadata['Name'])] = dist.version
        for item in dist.requires or []:
            dep = Requirement(item)
            if not dep.marker or any(dep.marker.evaluate({'extra': extra}) for extra in extras | {''}):
                pending.append((dep, set(dep.extras)))
    return ''.join(f'{name}=={version}\n' for name, version in sorted(found.items()))


root = Path(__file__).resolve().parents[1] / 'backend'
prod = (root / 'requirements.in').read_text().splitlines()
dev = [r for r in (root / 'requirements-dev.in').read_text().splitlines() if not r.startswith('-r')]
(root / 'requirements.txt').write_text(lock(prod), encoding='utf-8')
(root / 'requirements-dev.txt').write_text(lock(prod + dev), encoding='utf-8')
