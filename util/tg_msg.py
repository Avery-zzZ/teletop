from typing import List
import re

from telethon.tl.types import ReactionCount


def get_not_neg_react_num(reacts: List[ReactionCount]) -> int:
    result = 0
    for react in reacts:
        if _not_neg_react(react.reaction.emoticon):
            result += react.count
    return result


def _not_neg_react(emoji: str) -> bool:
    if emoji in ["💩", "👎", "🤮", "🖕"]:
        return False
    return True


_replace_dict = {"\n": "|", "[": "(", "]": ")", "#": ""}


def get_msg_text(raw: str) -> str:
    raw = re.sub(r'\n+', '\n', raw)
    raw = raw.replace(" ", "")
    if len(raw) == 0:
        return "no text message"
    for k, v in _replace_dict.items():
        raw = raw.replace(k, v)
    return raw[:255]