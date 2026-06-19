from hyperot import events
from hyperot.listener import Actions

from .types import *
import assets


class AgentCoreBase:
    tools = [
        Function(
            "send_group_msg", "向指定的群组发送消息，会返回被发送消息的message_id，可以用于引用回复、撤回等操作",
            args={
                "group_id": Para("integer", "目标群组的id,与事件中的`group_id`对应"),
                "message": MESSAGE_OBJECT
            }
        ),
        Function(
            "send_private_msg",
            "向指定的用户私聊发送消息（需要有对方的好友哦），会返回被发送消息的message_id，可以用于引用回复、撤回等操作",
            args={
                "user_id": Para("integer", "目标用户的id,与事件中的`user_id`对应"),
                "message": MESSAGE_OBJECT
            }
        ),
        Function(
            "del_msg",
            "撤回消息，只可以撤回你自己发送的哦",
            args={
                "message_id": Para("integer", "目标消息的id,与事件中和发送回报的`message_id`对应"),
            }
        ),
        Function(
            "get_group_info",
            "获取群信息",
            args={
                "group_id": Para("integer", "目标群组的id,与事件中的`group_id`对应"),
            }
        ),
        Function(
            "get_stranger_info",
            "获取用户信息",
            args={
                "user_id": Para("integer", "目标用户的id,与事件中的`user_id`对应"),
            }
        ),
        Function(
            "get_msg",
            "获取消息信息，这个消息可能是你没有收到但是被别人提及的消息",
            args={
                "message_id": Para("integer", "目标消息的id,与事件中的`message_id`对应"),
            }
        ),
        Function(
            "send_group_face",
            "向指定聊群发送一个表情包",
            args={
                "group_id": Para("integer", "目标群组的id,与事件中的`group_id`对应"),
                "face": Para("string", "表情包的文件名", assets.Face.all)
            }
        ),
        Function(
            "send_private_face",
            "向指定用户饲料发送一个表情包",
            args={
                "user_id": Para("integer", "目标用户的id,与事件中的`user_id`对应"),
                "face": Para("string", "表情包的文件名", assets.Face.all)
            }
        ),
        Function(
            "read_image",
            "阅读图片内容并获取描述",
            args={
                "url": Para("string", "消息上报中图片消息中的url"),
            }
        ),
        Function(
            "clear",
            "用总结性的信息代替完整聊天历史",
            args={
                "content": Para("string", "总结后的全部内容"),
            }
        )
    ]

    def __init__(self, bot_api: Actions, **kwargs):
        self.bot_api = bot_api

        ...

    async def event_handler(self, event: events.Event):
        pass

    async def image_handler(self, url: str):
        pass


system_prompt = assets.system_prompt
