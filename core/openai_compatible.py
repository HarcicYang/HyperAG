import json
import math
import time
import asyncio
import httpx
from io import BytesIO
from typing import Union
import moondream as md
from PIL import Image
from openai import OpenAI

import hyperot.segments
from hyperot.listener import Actions
from hyperot import events, configurator, hyperogger, segments
from hyperot.common import Message
from openai.types.admin.organization import role

from . import AgentCoreBase, system_prompt

import assets

config = configurator.BotConfig.get("hyper-bot")
logger = hyperogger.Logger()
logger.set_level(config.log_level)

lock = asyncio.Lock()


class CoreOpenAI(AgentCoreBase):
    def __init__(self, bot_api: Actions, key: str, model: str, base_url: str = ""):
        super().__init__(bot_api)
        self.model = model
        if base_url == "":
            self._oai = OpenAI(api_key=key)
        else:
            self._oai = OpenAI(
                api_key=key,
                base_url=base_url
            )
        self.tools = [i.serialize_openai() for i in super().tools]
        self.history: list = [{"role": "system", "content": system_prompt}]
        try:
            with open("history.json", "r") as f:
                self.history = json.load(f)
                self.history[0]["content"] = system_prompt
        except FileNotFoundError:
            pass

        self.working = False

    async def save(self):
        with open("history.json", "w") as f:
            json.dump(self.history, f, indent=2)

    async def event_handler(self, event: Union[events.Event, str], tool_choice: str = "auto"):
        while self.working:
            await asyncio.sleep(0.01)
        self.working = True
        await self._event_handler(event, tool_choice)
        self.working = False

    async def create_msg(self, raw_mess: dict) -> Message:
        new_mess = []
        for j in raw_mess:
            print(raw_mess)
            seg_type = j["params"]["seg"]
            match seg_type:
                case "text":
                    new_mess.append(segments.Text(j["params"].get("text") or j.get("text")))
                case "at":
                    new_mess.append(segments.At(j["params"].get("qq") or j.get("qq")))
                case "reply":
                    new_mess.append(segments.Reply(j["params"].get("id") or j.get("id")))
                case _:
                    raise NotImplementedError
        return Message(*new_mess)

    async def _event_handler(self, event: Union[events.Event, str], tool_choice: str = "auto"):
        data = event if isinstance(event, str) else json.dumps(event.data)
        logger.info(data)
        self.history.append({"role": "user", "content": data})
        resp = self._oai.chat.completions.create(
            model=self.model,
            messages=self.history,
            tools=self.tools,
            tool_choice=tool_choice,
        )
        mess = resp.choices[0].message
        call = mess.tool_calls
        logger.info(str(mess))
        logger.info(str(call))
        if call:
            self.history.append(mess.to_dict())
            for i in call:
                name = i.function.name
                try:
                    params = json.loads(i.function.arguments)
                except json.decoder.JSONDecodeError as e:
                    logger.error("错误的JSON，重试..." + repr(e))
                    self.history.pop(len(self.history) - 1)
                    self.history.pop(len(self.history) - 1)
                    await self._event_handler(event)
                    return
                match name:
                    case "send_group_msg":
                        group_id = params.get("group_id")
                        new_mess = await self.create_msg(params.get("message"))
                        await asyncio.sleep(math.log(len(str(new_mess)) + 3) * 0.5)
                        rs = await self.bot_api.send(group_id=group_id, message=new_mess)
                        rs = rs.raw
                    case "send_private_msg":
                        user_id = params.get("user_id")
                        new_mess = await self.create_msg(params.get("message"))
                        rs = await self.bot_api.send(user_id=user_id, message=new_mess)
                        rs = rs.raw
                    case "del_msg":
                        msg_id = params.get("message_id")
                        await self.bot_api.del_message(msg_id)
                        rs = "(无返回)"
                    case "get_group_info":
                        group_id = params.get("group_id")
                        rs = await self.bot_api.get_group_info(group_id)
                        rs = rs.raw
                    case "get_stranger_info":
                        user_id = params.get("user_id")
                        rs = await self.bot_api.get_stranger_info(user_id)
                        rs = rs.raw
                    case "get_msg":
                        message_id = params.get("message_id")
                        rs = await self.bot_api.get_msg(message_id)
                        rs = rs.raw
                    case "send_group_face":
                        group_id = params.get("group_id")
                        file = getattr(assets.Face, params.get("face", "KIANA_EATING"))
                        rs = await self.bot_api.send(
                            group_id=group_id, message=Message(segments.Image(file=file, summary="[动画表情]"))
                        )
                        rs = rs.raw
                    case "send_user_face":
                        user_id = params.get("user_id")
                        file = getattr(assets.Face, params.get("face", "KIANA_EATING"))
                        rs = await self.bot_api.send(
                            user_id=user_id, message=Message(segments.Image(file=file, summary="[动画表情]"))
                        )
                        rs = rs.raw
                    case "read_image":
                        url = params.get("url")
                        if "deepseek" in self.model:
                            rs = await self.ds_image_handler(url)
                        else:
                            rs = await self.image_handler(url)
                    case "clear":
                        content = params.get("content")
                        self.history = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": "SYSTEM -- 先前消息的全部总结 --"},
                            {"role": "assistant", "content": content}
                        ]
                        return
                    case _:
                        raise NotImplementedError
                self.history.append({"role": "tool", "tool_call_id": i.id, "name": i.function.name, "content": str(rs)})
            sed_resp = self._oai.chat.completions.create(
                model=self.model,
                messages=self.history,
            )
            fin_mess = sed_resp.choices[0].message
            self.history.append(fin_mess.to_dict())
            logger.info(str(fin_mess))
            asyncio.create_task(self.save())

    async def image_handler(self, url: str):
        raise NotImplementedError

    @staticmethod
    async def ds_image_handler(url: str) -> str:
        try:
            model = md.vl(api_key=config.others.get("moondream_key"),local=config.others.get("moondream_local"))
            data = httpx.get(url).content
            image = Image.open(BytesIO(data))
            caption = model.caption(image)["caption"]
        except Exception as e:
            print(repr(e))
            caption = "（网络不太好，看不到）"
        return caption
