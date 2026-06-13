import time

import asyncio
from hyperot import configurator

from cfgr.manager import Serializers  # Maybe I've forgotten sth when coding for ucfgr? IDK.

try:
    configurator.BotConfig.load_from("config.json", Serializers.JSON, "hyper-bot")
except FileNotFoundError:
    configurator.BotConfig.create_and_write("config.json", Serializers.JSON)
    print("没有找到配置文件，已自动创建，请填写后重启")
    exit(-1)
if True:
    from hyperot.adapters import builtins as adp

    adp.load_onebot()

    from hyperot import listener, hyperogger, Client
    from hyperot.events import *
    from hyperot.common import Message
    from hyperot.segments import *

    from core.openai_compatible import CoreOpenAI

config = configurator.BotConfig.get("hyper-bot")
logger = hyperogger.Logger()
logger.set_level(config.log_level)


ag: CoreOpenAI = None

ANY_EVENT = Union[
    MessageEvent,
    NoticeEvent,
    RequestEvent
]


async def heartbeat():
    global ag
    while True:
        time.sleep(60 * 5)
        await ag.event_handler("<Heartbeat> QQ上什么也没有发生，但是如果你需要，你也许可以借助这个机会发消息。心跳事件每5min发生一次。")


heartbeat_task: asyncio.Task = None


async def handler_msg(event: ANY_EVENT, actions: listener.Actions):
    global ag, heartbeat_task
    if isinstance(event, GroupMessageEvent) and int(event.group_id) not in [623371208, 983497968]:
        return

    if ag is None:
        ag = CoreOpenAI(
            bot_api=actions,
            key=str(config.others.get("openai_key")),
            model=str(config.others.get("openai_model")),
            base_url=str(config.others.get("openai_endpoint")),
        )

    if heartbeat_task is None:
        heartbeat_task = asyncio.create_task(heartbeat())

    await ag.event_handler(event)


with Client() as cli:
    cli.subscribe(handler_msg, GroupMessageEvent)
    cli.subscribe(handler_msg, PrivateMessageEvent)
    cli.subscribe(handler_msg, GroupMemberIncreaseEvent)
    cli.subscribe(handler_msg, GroupRecallEvent)
    cli.run()


