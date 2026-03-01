from __future__ import annotations

from typing import Any, Optional, Sequence

try:
    import astrbot.api.message_components as Comp  # type: ignore
    from astrbot.api.event import AstrMessageEvent, filter  # type: ignore
    from astrbot.api.star import Context, Star, register  # type: ignore
except Exception:  # pragma: no cover
    Comp = None  # type: ignore[assignment]
    AstrMessageEvent = Any  # type: ignore[misc,assignment]

    def register(*_: Any, **__: Any):  # type: ignore[misc]
        def _decorator(cls: Any) -> Any:
            return cls

        return _decorator

    class Star:  # type: ignore[no-redef]
        def __init__(self, context: Any):
            self.context = context

    class Context:  # type: ignore[no-redef]
        pass

    class filter:  # type: ignore[no-redef]
        @staticmethod
        def on_decorating_result(*_: Any, **__: Any):
            def _decorator(fn: Any) -> Any:
                return fn

            return _decorator


_SENTENCE_DELIMS = set("。！？!?；;，,、")
_SEPARATOR = "\n\n"


def _split_text(text: str) -> list[str]:
    if not text:
        return []
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    buf: list[str] = []
    out: list[str] = []

    def flush() -> None:
        part = "".join(buf).strip()
        buf.clear()
        if part:
            out.append(part)

    for ch in text:
        if ch == "\n":
            flush()
            continue
        buf.append(ch)
        if ch in _SENTENCE_DELIMS:
            flush()
    flush()
    return out


def _is_plain_component(component: Any) -> bool:
    if Comp is None:
        return False
    plain_type = getattr(Comp, "Plain", None)
    if plain_type is None:
        return False
    return isinstance(component, plain_type)


def _plain_text(component: Any) -> Optional[str]:
    text = getattr(component, "text", None)
    if isinstance(text, str):
        return text
    return None


def _new_plain(text: str) -> Any:
    if Comp is None:
        return text
    plain_type = getattr(Comp, "Plain", None)
    if plain_type is None:
        return text
    return plain_type(text)


def _split_chain(chain: Sequence[Any], separator: str) -> tuple[list[Any], bool]:
    out: list[Any] = []
    changed = False
    for component in chain:
        if _is_plain_component(component):
            text = _plain_text(component) or ""
            parts = _split_text(text)
            if len(parts) <= 1:
                out.append(component)
                continue
            changed = True
            for idx, part in enumerate(parts):
                if idx != len(parts) - 1 and separator:
                    out.append(_new_plain(part + separator))
                else:
                    out.append(_new_plain(part))
            continue
        out.append(component)
    return out, changed


@register("duanju", "echoflux", "发送消息前对文本段断句（保留非文本段）", "1.1.0")
class DuanJuPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent) -> None:
        result = event.get_result()
        chain = getattr(result, "chain", None)
        if not isinstance(chain, list) or not chain:
            return

        split_chain, changed = _split_chain(chain, _SEPARATOR)
        if not changed:
            return
        chain[:] = split_chain
