import contextvars
import uuid

correlation_id_ctx = contextvars.ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    cid = correlation_id_ctx.get()
    if not cid:
        cid = str(uuid.uuid4())
        correlation_id_ctx.set(cid)
    return cid


class CorrelationIdMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        raw_cid = headers.get(b"x-correlation-id")
        if raw_cid:
            corr_id = raw_cid.decode("latin1")
        else:
            corr_id = str(uuid.uuid4())

        correlation_id_ctx.set(corr_id)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                resp_headers = list(message.get("headers", []))
                resp_headers.append((b"x-correlation-id", corr_id.encode("latin1")))
                message["headers"] = resp_headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
