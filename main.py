from __future__ import annotations

from typing import Any, List, Optional, Sequence, Tuple

try:
    from nakuru.entities.components import Plain  # type: ignore
except Exception:  # pragma: no cover
    Plain = None  # type: ignore[misc,assignment]

try:
    from cores.qqbot.global_object import AstrMessageEvent  # type: ignore
except Exception:  # pragma: no cover
    AstrMessageEvent = Any  # type: ignore[misc,assignment]


_SENTENCE_DELIMS = set("\n\n")
_SEPARATOR = "\n\n"


def _split_text(text: str) -> List[str]:
    if not text:
        return []
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    buf: List[str] = []
    out: List[str] = []

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
    if Plain is None:
        return False
    return isinstance(component, Plain)


def _plain_text(component: Any) -> Optional[str]:
    text = getattr(component, "text", None)
    if isinstance(text, str):
        return text
    return None


def _new_plain(text: str) -> Any:
    if Plain is None:
        return text
    return Plain(text)


def _split_chain(chain: Sequence[Any], separator: str) -> tuple[List[Any], bool]:
    out: List[Any] = []
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


class Main:
    def __init__(self, context: Any = None, **_: Any) -> None:
        self.context = context

    def run(self, ame: AstrMessageEvent):
        message_str = (getattr(ame, "message_str", "") or "").strip()
        separator = _SEPARATOR

        message_obj = getattr(ame, "message_obj", None)
        try:
            self_id = getattr(message_obj, "self_id", None)
            user_id = getattr(message_obj, "user_id", None)
            if self_id is not None and user_id is not None and str(self_id) == str(user_id):
                return False, None
        except Exception:
            pass

        chain = getattr(message_obj, "message", None)
        if isinstance(chain, list) and chain:
            split_chain, changed = _split_chain(chain, separator)
            if not changed:
                return False, None
            return True, tuple([True, split_chain, "duanju"])

        parts = _split_text(message_str)
        if len(parts) <= 1:
            return False, None
        return True, tuple([True, separator.join(parts), "duanju"])

    def info(self):
        return {
            "name": "断句",
            "desc": "对所有消息的文本段断句，并尽量保留原消息链中的非文本段（图片/At等）。",
            "help": "自动：对所有消息的文本段按常见标点断句。\n说明：仅对文本段断句；图片/语音/At 等会原样保留并按原顺序返回；如果无需断句（只有一句），则不响应。",
            "version": "v1.0.0",
            "author": "echoflux",
            "repo": "https://github.com/echoflux/astrbot_spilt",
        }
