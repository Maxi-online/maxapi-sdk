from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Iterable, Sequence

from .callback_schema import extract_callback_mapping, extract_callback_value
from .filters import ensure_filter
from .fsm import FSMMiddleware, MemoryStorage
from .middlewares import BaseMiddleware, FunctionMiddleware, MiddlewareHandler
from .runners import PollingRunner, WebhookRunner
from .types import Message, Update, UpdateType

HandlerCallable = Callable[[Any], Awaitable[Any]]
FilterCallable = Callable[[Any], Awaitable[bool] | bool]
MiddlewareCallable = Callable[[MiddlewareHandler, Any, dict[str, Any]], Awaitable[Any] | Any]


@dataclass(slots=True)
class HandlerSpec:
    update_type: UpdateType | str
    callback: HandlerCallable
    filters: list[FilterCallable] = field(default_factory=list)


class BaseEvent:
    def __init__(self, *, bot, update: Update, raw_data: dict[str, Any] | None = None) -> None:
        self.bot = bot
        self.update = update
        self.raw_data = raw_data or {}
        self.update_type = update.update_type

    @property
    def chat_id(self) -> int | None:
        if self.update.chat_id is not None:
            return self.update.chat_id
        message = getattr(self.update, "message", None)
        if message is not None:
            if message.chat_id is not None:
                return message.chat_id
            if message.recipient is not None:
                return message.recipient.chat_id
        callback = getattr(self.update, "callback", None)
        if callback is not None and callback.message is not None:
            callback_message = callback.message
            if callback_message.chat_id is not None:
                return callback_message.chat_id
            if callback_message.recipient is not None:
                return callback_message.recipient.chat_id
        return None

    @property
    def user_id(self) -> int | None:
        if self.update.user_id is not None:
            return self.update.user_id
        message = getattr(self.update, "message", None)
        if message is not None and message.sender is not None:
            return message.sender.user_id
        callback = getattr(self.update, "callback", None)
        if callback is not None and callback.user is not None:
            return callback.user.user_id
        return None


class MessageEvent(BaseEvent):
    @property
    def message(self) -> Message:
        if self.update.message is None:
            raise RuntimeError("В событии отсутствует message.")
        return self.update.message


class CallbackEvent(BaseEvent):
    @property
    def callback_id(self) -> str | None:
        if self.update.callback is not None and self.update.callback.callback_id is not None:
            return self.update.callback.callback_id
        return self.update.callback_id

    @property
    def callback(self):
        return self.update.callback

    @property
    def message(self) -> Message | None:
        if self.update.callback is not None:
            return self.update.callback.message
        return None

    @property
    def payload(self) -> Any:
        if self.update.callback is None:
            return None
        return self.update.callback.payload

    @property
    def payload_text(self) -> str | None:
        return extract_callback_value(self.payload)

    @property
    def payload_dict(self) -> dict[str, Any] | None:
        return extract_callback_mapping(self.payload)

    def unpack(self, schema):
        return schema.unpack(self.payload)

    async def answer(
        self,
        *,
        notification: str | None = None,
        message: dict[str, Any] | None = None,
        keyboard: Any | None = None,
    ):
        callback_id = self.callback_id
        if callback_id is None:
            raise RuntimeError("В callback-событии отсутствует callback_id.")
        from .types import MessageBody

        message_body = MessageBody.model_validate(message) if message is not None else None
        return await self.bot.answer_callback(
            callback_id,
            notification=notification,
            message=message_body,
            keyboard=keyboard,
        )


class Router:
    def __init__(self) -> None:
        self.handlers: dict[str, list[HandlerSpec]] = {}
        self.routers: list[Router] = []
        self.middlewares: list[BaseMiddleware] = []
        self.plugins: list[Any] = []
        self.bot = None

    def include_router(self, router: "Router") -> None:
        self.routers.append(router)

    def include_plugin(self, plugin) -> Any:
        plugin.setup(self)
        self.plugins.append(plugin)
        return plugin

    def include_plugins(self, *plugins) -> tuple[Any, ...]:
        return tuple(self.include_plugin(plugin) for plugin in plugins)

    def use(self, middleware: BaseMiddleware | MiddlewareCallable) -> BaseMiddleware:
        prepared = middleware if isinstance(middleware, BaseMiddleware) else FunctionMiddleware(middleware)
        self.middlewares.append(prepared)
        return prepared

    def add_middleware(self, middleware: BaseMiddleware | MiddlewareCallable) -> BaseMiddleware:
        return self.use(middleware)

    def _register_handler(
        self,
        update_type: UpdateType | str,
        callback: HandlerCallable,
        *filters: FilterCallable,
    ) -> HandlerCallable:
        normalized_type = update_type.value if hasattr(update_type, "value") else str(update_type)
        self.handlers.setdefault(normalized_type, []).append(
            HandlerSpec(
                update_type=normalized_type,
                callback=callback,
                filters=list(filters),
            )
        )
        return callback

    def on(self, update_type: UpdateType | str, *filters: FilterCallable):
        normalized_type = update_type.value if hasattr(update_type, "value") else str(update_type)

        def decorator(func: HandlerCallable) -> HandlerCallable:
            self.handlers.setdefault(normalized_type, []).append(
                HandlerSpec(update_type=normalized_type, callback=func, filters=list(filters))
            )
            return func

        return decorator

    def message_created(self, *filters: FilterCallable):
        return self.on(UpdateType.MESSAGE_CREATED, *filters)

    def message_callback(self, *filters: FilterCallable):
        return self.on(UpdateType.MESSAGE_CALLBACK, *filters)

    def message_edited(self, *filters: FilterCallable):
        return self.on(UpdateType.MESSAGE_EDITED, *filters)

    def message_removed(self, *filters: FilterCallable):
        return self.on(UpdateType.MESSAGE_REMOVED, *filters)

    def bot_started(self, *filters: FilterCallable):
        return self.on(UpdateType.BOT_STARTED, *filters)

    def bot_added(self, *filters: FilterCallable):
        return self.on(UpdateType.BOT_ADDED, *filters)

    def bot_removed(self, *filters: FilterCallable):
        return self.on(UpdateType.BOT_REMOVED, *filters)

    def bot_stopped(self, *filters: FilterCallable):
        return self.on(UpdateType.BOT_STOPPED, *filters)

    def user_added(self, *filters: FilterCallable):
        return self.on(UpdateType.USER_ADDED, *filters)

    def user_removed(self, *filters: FilterCallable):
        return self.on(UpdateType.USER_REMOVED, *filters)

    def message_handler(self, *filters: FilterCallable):
        return self.message_created(*filters)

    def callback_handler(self, *filters: FilterCallable):
        return self.message_callback(*filters)

    def callback_query_handler(self, *filters: FilterCallable):
        return self.message_callback(*filters)

    def edited_message_handler(self, *filters: FilterCallable):
        return self.message_edited(*filters)

    def removed_message_handler(self, *filters: FilterCallable):
        return self.message_removed(*filters)

    def register_message_handler(self, callback: HandlerCallable, *filters: FilterCallable) -> HandlerCallable:
        return self._register_handler(UpdateType.MESSAGE_CREATED, callback, *filters)

    def register_callback_handler(self, callback: HandlerCallable, *filters: FilterCallable) -> HandlerCallable:
        return self._register_handler(UpdateType.MESSAGE_CALLBACK, callback, *filters)


class Dispatcher(Router):
    def __init__(self, *, storage=None) -> None:
        super().__init__()
        self.fsm_storage = storage
        if self.fsm_storage is not None:
            self.use(FSMMiddleware(self.fsm_storage))

    def setup_fsm(self, storage=None):
        self.fsm_storage = storage or MemoryStorage()
        self.middlewares = [
            middleware for middleware in self.middlewares if not isinstance(middleware, FSMMiddleware)
        ]
        self.middlewares.insert(0, FSMMiddleware(self.fsm_storage))
        return self.fsm_storage

    async def process_update(self, payload: Update | dict[str, Any], *, bot) -> None:
        self.bot = bot
        bot.dispatcher = self
        update = payload if isinstance(payload, Update) else Update.model_validate(payload)
        if update.message is not None:
            update.message.bind_bot(bot)
        if update.callback is not None and update.callback.message is not None:
            update.callback.message.bind_bot(bot)
        event = self._build_event(bot=bot, update=update, raw_data=payload if isinstance(payload, dict) else None)
        await self._dispatch_router(self, event, inherited_middlewares=[])

    async def _dispatch_router(
        self,
        router: Router,
        event: BaseEvent,
        *,
        inherited_middlewares: Sequence[BaseMiddleware],
    ) -> None:
        update_type = event.update.update_type
        normalized_type = update_type.value if hasattr(update_type, "value") else str(update_type)
        middleware_chain = [*inherited_middlewares, *router.middlewares]
        for handler in router.handlers.get(normalized_type, []):
            if await self._filters_pass(handler.filters, event):
                data = self._build_handler_data(event=event, router=router)
                await self._call_with_middlewares(
                    callback=handler.callback,
                    event=event,
                    data=data,
                    middlewares=middleware_chain,
                )
        for child in router.routers:
            child.bot = self.bot
            await self._dispatch_router(
                child,
                event,
                inherited_middlewares=middleware_chain,
            )

    async def _filters_pass(self, filters: Iterable[FilterCallable], event: BaseEvent) -> bool:
        for item in filters:
            prepared = ensure_filter(item)
            result = await prepared(event)
            if not result:
                return False
        return True

    async def _call_with_middlewares(
        self,
        *,
        callback: HandlerCallable,
        event: BaseEvent,
        data: dict[str, Any],
        middlewares: Sequence[BaseMiddleware],
    ) -> Any:
        async def terminal(current_event: BaseEvent, current_data: dict[str, Any]) -> Any:
            return await self._call_handler(callback, current_event, current_data)

        handler = terminal
        for middleware in reversed(middlewares):
            next_handler = handler

            async def wrapped(
                current_event: BaseEvent,
                current_data: dict[str, Any],
                *,
                current_middleware: BaseMiddleware = middleware,
                current_next: MiddlewareHandler = next_handler,
            ) -> Any:
                return await current_middleware(current_next, current_event, current_data)

            handler = wrapped
        return await handler(event, data)

    async def _call_handler(
        self,
        callback: HandlerCallable,
        event: BaseEvent,
        data: dict[str, Any],
    ) -> Any:
        signature = inspect.signature(callback)
        positional_args: list[Any] = []
        keyword_args: dict[str, Any] = {}
        used_event_fallback = False

        for parameter in signature.parameters.values():
            if parameter.kind == inspect.Parameter.VAR_POSITIONAL:
                continue
            if parameter.kind == inspect.Parameter.VAR_KEYWORD:
                keyword_args.update(data)
                continue
            value_provided = False
            value: Any = None
            if parameter.name in data:
                value = data[parameter.name]
                value_provided = True
            elif parameter.name in {"event", "message_event", "callback_event"}:
                value = event
                value_provided = True
            elif not used_event_fallback:
                value = event
                value_provided = True
                used_event_fallback = True
            elif parameter.default is inspect.Parameter.empty:
                raise TypeError(
                    f"Не удалось внедрить обязательный аргумент '{parameter.name}' "
                    f"для handler {callback.__name__}."
                )

            if not value_provided:
                continue
            if parameter.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            ):
                positional_args.append(value)
            else:
                keyword_args[parameter.name] = value

        result = callback(*positional_args, **keyword_args)
        if inspect.isawaitable(result):
            return await result
        return result

    def _build_handler_data(self, *, event: BaseEvent, router: Router) -> dict[str, Any]:
        message = getattr(event, "message", None)
        callback = getattr(event.update, "callback", None)
        callback_event = event if isinstance(event, CallbackEvent) else None
        return {
            "bot": event.bot,
            "callback": callback,
            "callback_event": callback_event,
            "callback_payload": callback_event.payload if callback_event is not None else None,
            "callback_payload_dict": callback_event.payload_dict if callback_event is not None else None,
            "callback_payload_text": callback_event.payload_text if callback_event is not None else None,
            "chat_id": event.chat_id,
            "data": {},
            "dispatcher": self,
            "event": event,
            "message": message,
            "message_event": event if isinstance(event, MessageEvent) else None,
            "raw_data": event.raw_data,
            "router": router,
            "update": event.update,
            "user_id": event.user_id,
        }

    def _build_event(self, *, bot, update: Update, raw_data: dict[str, Any] | None) -> BaseEvent:
        update_type = update.update_type.value if hasattr(update.update_type, "value") else str(update.update_type)
        if update_type in {
            UpdateType.MESSAGE_CREATED.value,
            UpdateType.MESSAGE_EDITED.value,
            UpdateType.MESSAGE_REMOVED.value,
            UpdateType.BOT_STARTED.value,
            UpdateType.BOT_ADDED.value,
            UpdateType.BOT_REMOVED.value,
            UpdateType.BOT_STOPPED.value,
            UpdateType.USER_ADDED.value,
            UpdateType.USER_REMOVED.value,
        }:
            return MessageEvent(bot=bot, update=update, raw_data=raw_data)
        if update_type == UpdateType.MESSAGE_CALLBACK.value:
            return CallbackEvent(bot=bot, update=update, raw_data=raw_data)
        return BaseEvent(bot=bot, update=update, raw_data=raw_data)

    async def start_polling(
        self,
        bot,
        *,
        limit: int = 100,
        timeout: int = 30,
        allowed_updates: Iterable[UpdateType | str] | None = None,
        retry_delay: float = 2.0,
    ) -> None:
        bot.dispatcher = self
        if bot.auto_check_subscriptions:
            subscriptions = await bot.get_subscriptions()
            if subscriptions.subscriptions:
                raise RuntimeError(
                    "Обнаружены активные webhook-подписки. Удалите их через bot.delete_webhook()."
                )
        runner = PollingRunner(
            bot=bot,
            dispatcher=self,
            limit=limit,
            timeout=timeout,
            allowed_updates=allowed_updates,
            retry_delay=retry_delay,
        )
        await runner.start()

    async def run_polling(
        self,
        bot,
        *,
        limit: int = 100,
        timeout: int = 30,
        allowed_updates: Iterable[UpdateType | str] | None = None,
        retry_delay: float = 2.0,
    ) -> None:
        await self.start_polling(
            bot,
            limit=limit,
            timeout=timeout,
            allowed_updates=allowed_updates,
            retry_delay=retry_delay,
        )

    def create_webhook_app(
        self,
        *,
        bot,
        path: str = "/webhook",
        secret: str | None = None,
    ):
        bot.dispatcher = self
        runner = WebhookRunner(bot=bot, dispatcher=self, path=path, secret=secret)
        return runner.create_app()

    async def handle_webhook(
        self,
        *,
        bot,
        host: str = "127.0.0.1",
        port: int = 8080,
        path: str = "/webhook",
        secret: str | None = None,
        log_level: str = "info",
    ) -> None:
        bot.dispatcher = self
        runner = WebhookRunner(
            bot=bot,
            dispatcher=self,
            host=host,
            port=port,
            path=path,
            secret=secret,
            log_level=log_level,
        )
        await runner.start()
