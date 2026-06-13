import asyncio
from typing import Union
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
    from hyperot.events import GroupMessageEvent
    from hyperot.common import Message
    from hyperot.segments import *

    from core.openai_compatible import CoreOpenAI

config = configurator.BotConfig.get("hyper-bot")
logger = hyperogger.Logger()
logger.set_level(config.log_level)


ag: CoreOpenAI = None

async def handler_msg(event: GroupMessageEvent, actions: listener.Actions):
    global ag
    if int(event.group_id) not in [623371208, 983497968]:
        return

    if ag is None:
        ag = CoreOpenAI(
            bot_api=actions,
            key=config.others.get("openai_key"),
            model=config.others.get("openai_model"),
            base_url=config.others.get("openai_endpoint"),
        )

    await ag.event_handler(event)


with Client() as cli:
    cli.subscribe(handler_msg, GroupMessageEvent)
    cli.run()

listener.run()
