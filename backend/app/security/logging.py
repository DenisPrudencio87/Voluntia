"""Conserva acceso/estado HTTP sin guardar tokens de enlaces en query strings."""

import logging


class RedactAccessQuery(logging.Filter):
    def filter(self, record):
        args = record.args
        # Formato de uvicorn.access: cliente, método, ruta, versión HTTP, estado.
        if isinstance(args, tuple) and len(args) == 5 and isinstance(args[2], str):
            record.args = (*args[:2], args[2].split("?", 1)[0], *args[3:])
        return True
