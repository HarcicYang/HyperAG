from dataclasses import dataclass, field
from typing import Literal



@dataclass
class Para:
    type: Literal["string", "number", "boolean", "integer"]
    desc: str = ""
    enum: list[str] = field(default_factory=list)

    def serialize_openai(self) -> dict:
        return {
            "type": self.type,
            "description": self.desc,
        } if self.enum == [] else {
            "type": self.type,
            "description": self.desc,
            "enum": self.enum,
        }


@dataclass
class ParaObject:
    desc: str
    args: dict[str, Para]

    def serialize_openai(self) -> dict:
        paras = {}
        for i in self.args:
            paras[i] = self.args[i].serialize_openai()
        return {
            "type": "object",
            "description": self.desc,
            "properties": {
                "params": paras
            }
        }


@dataclass
class ParaArrayObject(Para):
    type: str = "array"
    objs: list[ParaObject] = field(default_factory=list)

    def serialize_openai(self) -> dict:
        return {
            "type": "array",
            "items": {
                "anyOf":
                    [
                        i.serialize_openai() for i in self.objs
                    ]
            },
        }


@dataclass
class Function:
    name: str
    desc: str
    args: dict[str, Para]

    def serialize_openai(self) -> dict:
        paras = {}
        for i in self.args:
            paras[i] = self.args[i].serialize_openai()
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.desc,
                "parameters": {
                    "type": "object",
                    "properties": paras
                }
            }
        }


SEG_TEXT = ParaObject(
    "文字类型的消息段",
    {
        "seg": Para("string", "消息段类型，必须为text"),
        "text": Para("string", "文本内容")
    }
)

SEG_AT = ParaObject(
    "'@'类型的消息段，会在聊天中'@'对应的user_id的用户",
    {
        "seg": Para("string", "消息段类型，必须为at"),
        "qq": Para("string", "就是user_id，与事件上报对应")
    }
)

SEG_REPLY = ParaObject(
    "回复类型的消息段，会在聊天中显示对被回复消息的引用，如果需要，一般放在第一位",
    {
        "seg": Para("string", "消息段类型，必须为reply"),
        "id": Para("string", "就是message_id，与事件上报对应")
    }
)

MESSAGE_OBJECT = ParaArrayObject(
    desc="调用工具需要的标准消息类型，由消息段组合而成。目前并没有支持全部的消息段，只支持 SEG_TEXT SEG_AT 和 SEG_REPLY",
    objs=[SEG_TEXT, SEG_AT, SEG_REPLY]
)