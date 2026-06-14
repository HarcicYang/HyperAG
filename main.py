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
acted = 0


ANY_EVENT = Union[
    MessageEvent,
    NoticeEvent,
    RequestEvent
]


async def heartbeat():
    global ag, acted
    
    base_time = 5
    
    while True:
        last_acted = acted
        time.sleep(60 * base_time)
        await ag.event_handler(f"Heartbeat {base_time} mins")
        delta = acted - last_acted
        if delta == 0:
            base_time = base_time * 4
        elif 0 < delta / base_time <= 0.7:
            base_time = base_time * 2
        elif 0.7 < delta / base_time <= 1:
            base_time = base_time * 1
        elif 1 < delta / base_time <= 1.2:
            base_time = base_time  * 0.5
        elif 1.2 < delta / base_time <= 2:
            base_time = base_time * 0.25
        else:
            base_time = base_time * 0.12
        


heartbeat_task: asyncio.Task = None


async def handler_msg(event: ANY_EVENT, actions: listener.Actions):
    global acted
    global ag, heartbeat_task
    if isinstance(event, GroupMessageEvent) and int(event.group_id) not in [623371208, 983497968, 895857556, 991819754]:
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
    acted += 1


with Client() as cli:
    cli.subscribe(handler_msg, GroupMessageEvent)
    cli.subscribe(handler_msg, PrivateMessageEvent)
    cli.subscribe(handler_msg, GroupMemberIncreaseEvent)
    cli.subscribe(handler_msg, GroupRecallEvent)
    cli.subscribe(handler_msg, GroupMuteEvent)
    cli.run()


