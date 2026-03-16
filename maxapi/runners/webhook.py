from typing import Any

from ..exceptions import MaxConnection

try:  # pragma: no cover - optional dependency at import time
    from fastapi import FastAPI, Header, HTTPException, Request
except ImportError:  # pragma: no cover
    FastAPI = None
    Header = None
    HTTPException = None
    Request = None


class WebhookRunner:
    """Отдельный runtime-класс для webhook."""

    def __init__(
        self,
        *,
        bot,
        dispatcher,
        path: str = "/webhook",
        secret: str | None = None,
        host: str = "127.0.0.1",
        port: int = 8080,
        log_level: str = "info",
    ) -> None:
        self.bot = bot
        self.dispatcher = dispatcher
        self.path = path
        self.secret = secret
        self.host = host
        self.port = port
        self.log_level = log_level

    def create_app(self):
        if FastAPI is None or Header is None or HTTPException is None or Request is None:
            raise MaxConnection(
                "Для webhook runtime требуется fastapi. Установите maxapi[webhook]."
            )

        app = FastAPI()

        @app.post(self.path)
        async def handle_update(
            request: Request,
            x_max_bot_api_secret: str | None = Header(default=None),
        ) -> dict[str, Any]:
            if self.secret is not None and x_max_bot_api_secret != self.secret:
                raise HTTPException(status_code=403, detail="Invalid webhook secret")
            payload = await request.json()
            await self.dispatcher.process_update(payload, bot=self.bot)
            return {"ok": True}

        return app

    async def start(self) -> None:
        try:
            import uvicorn
        except ImportError as exc:  # pragma: no cover
            raise MaxConnection(
                "Для webhook runtime требуется uvicorn. Установите maxapi[webhook]."
            ) from exc
        app = self.create_app()
        config = uvicorn.Config(
            app=app,
            host=self.host,
            port=self.port,
            log_level=self.log_level,
        )
        server = uvicorn.Server(config)
        await server.serve()
