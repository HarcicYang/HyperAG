import agconfig

import asyncio
import math
import time
from typing import Optional, Callable
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

    from hyperot import listener, Client
    from hyperot.events import *
    from hyperot.common import Message
    from hyperot.segments import *

    from core.openai_compatible import CoreOpenAI

CONFIG = agconfig.BotConfig

config: CONFIG = configurator.BotConfig.get("hyper-bot")
logger = hyperogger.Logger()
logger.set_level(config.log_level)

ag: CoreOpenAI = None
acted = 0

NON_MSG_EVENT = Union[
    NoticeEvent,
    RequestEvent
]


async def heartbeat():
    global ag, acted

    base_time = 5

    while True:
        last_acted = acted
        await asyncio.sleep(60 * base_time)
        await ag.event_handler(f"Heartbeat {base_time} mins")
        delta = acted - last_acted
        if delta == 0:
            base_time = base_time * 4
        elif 0 < delta / base_time <= 0.7:
            base_time = base_time * 2
        elif 0.7 < delta / base_time <= 1:
            base_time = base_time * 1
        elif 1 < delta / base_time <= 1.2:
            base_time = base_time * 0.5
        elif 1.2 < delta / base_time <= 2:
            base_time = base_time * 0.25
        else:
            base_time = base_time * 0.12


async def auto_summarize():
    global ag
    while True:
        await asyncio.sleep(60 * 60 * 1)
        await ag.event_handler("SYSTEM: 请你总结以上全部消息，分条列出，随后调用`clear`工具以完成聊天总结。", "clear")


heartbeat_task: asyncio.Task = None
auto_summarize_task: asyncio.Task = None


async def serve(actions: listener.Actions):
    global ag, heartbeat_task, auto_summarize_task
    if ag is None:
        ag = CoreOpenAI(
            bot_api=actions,
            key=str(config.others.openai_key),
            model=str(config.others.openai_model),
            base_url=str(config.others.openai_endpoint),
        )

    if heartbeat_task is None:
        heartbeat_task = asyncio.create_task(heartbeat())
    if auto_summarize_task is None:
        auto_summarize_task = asyncio.create_task(auto_summarize())


async def general_handler(event: NON_MSG_EVENT, actions: listener.Actions):
    global acted, ag
    if hasattr(event, "group_id") and int(event.group_id) not in config.others.white:
        return

    await serve(actions)

    await ag.event_handler(event)
    acted += 1


class MessageCollector:
    def __init__(self, gid: int):
        self.collected = []
        self.gid = gid
        self.delay = 5.8
        self.doing_task: Optional[asyncio.Task] = None
        self.last_receive: float = 0
        self.active = False
        self.replying = False

    async def _sleep(self, callback: Callable):
        try:
            await asyncio.sleep(self.delay)
            self.replying = True
            logger.debug(f"{self.gid} : 完成收集，共{len(self.collected)}事件")
            await callback(str(self.collected))
            self.active = False
        except asyncio.CancelledError:
            pass

    async def update_sleep(self, last: float, length: int):
        rate = last / self.delay
        weight_length = 1 if length * 0.2 <= 1 else length * 0.2
        self.delay = (2 / 3) * (1 - math.cos(math.pi * rate)) + (1 / 3) * weight_length + 1
        if self.delay >= 12:
            self.delay = 12
        if self.delay <= 1:
            self.delay = 1
        logger.debug(f"{self.gid} : 调整延时为 {self.delay} s，比率 {rate}")

    async def collect(self, event: MessageEvent, callback: Callable):
        if not self.active or self.replying:
            return
        self.collected.append(json.dumps(event.data))
        logger.debug(f"{self.gid} : 收集 {event.data}")
        if isinstance(self.doing_task, asyncio.Task) and self.doing_task.done():
            self.doing_task = None
            # logger.debug(f"{self.gid} : 完成收集，共{len(self.collected)}事件")
        if isinstance(self.doing_task, asyncio.Task):
            self.doing_task.cancel()
        self.doing_task = asyncio.create_task(self._sleep(callback))
        if len(self.collected) > 1:
            await self.update_sleep(time.time() - self.last_receive, len(str(event.message)))
        else:
            length = len(str(event.message))
            weight_length = 1 if length * 0.2 <= 1 else length * 0.2
            self.delay = self.delay * weight_length
        self.last_receive = time.time()


collectors: dict[str, MessageCollector] = {}


async def grp_cb(ev: str):
    global acted
    await ag.event_handler(ev)
    acted += 1


async def message_handler(event: MessageEvent, actions: listener.Actions):
    global acted, ag
    if isinstance(event, GroupMessageEvent) and int(event.group_id) not in config.others.white:
        return

    await serve(actions)

    if isinstance(event, GroupMessageEvent):
        while str(event.group_id) in collectors.keys() and collectors[str(event.group_id)].replying:
            await asyncio.sleep(0.01)

        if str(event.group_id) not in collectors.keys():
            collectors[str(event.group_id)] = MessageCollector(event.group_id)
            collectors[str(event.group_id)].active = True
        await collectors[str(event.group_id)].collect(event, grp_cb)
        try:
            while collectors[str(event.group_id)].active:
                await asyncio.sleep(0.01)
            del collectors[str(event.group_id)]
        except KeyError:
            pass

        return

    await ag.event_handler(event)
    acted += 1


with Client() as cli:
    cli.subscribe(message_handler, GroupMessageEvent)
    cli.subscribe(message_handler, PrivateMessageEvent)
    cli.subscribe(general_handler, GroupMemberIncreaseEvent)
    cli.subscribe(general_handler, GroupRecallEvent)
    cli.subscribe(general_handler, GroupMuteEvent)
    cli.subscribe(general_handler, UnrecognizedEvent)  # I do think he can handle this
    cli.run()
