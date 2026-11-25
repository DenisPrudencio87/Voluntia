"""Limita bytes reales recibidos, incluyendo peticiones chunked sin Content-Length."""

from tempfile import SpooledTemporaryFile
from starlette.responses import JSONResponse


class BodyLimitMiddleware:
    def __init__(self, app, max_bytes=11 * 1024 * 1024):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] in ("GET", "HEAD", "OPTIONS"):
            return await self.app(scope, receive, send)
        response_started = False

        async def tracked_send(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            with SpooledTemporaryFile(max_size=1024 * 1024) as body:
                total = 0
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    chunk = message.get("body", b"")
                    total += len(chunk)
                    if total > self.max_bytes:
                        return await JSONResponse(
                            {"detail": "Solicitud demasiado grande"}, status_code=413
                        )(scope, receive, send)
                    body.write(chunk)
                    if not message.get("more_body", False):
                        break
                body.seek(0)
                finished = False

                async def replay():
                    nonlocal finished
                    if finished:
                        return await receive()
                    chunk = body.read(65536)
                    finished = body.tell() == total
                    return {
                        "type": "http.request",
                        "body": chunk,
                        "more_body": not finished,
                    }

                await self.app(scope, replay, tracked_send)
        except OSError:
            if response_started:
                raise
            await JSONResponse(
                {"detail": "No se pudo procesar la solicitud"}, status_code=503
            )(scope, receive, send)
