import json
import time

from openai import OpenAI

import hyperot.segments
from hyperot.listener import Actions
from hyperot import events, configurator, hyperogger, segments
from hyperot.common import Message
from . import AgentCoreBase, system_prompt

config = configurator.BotConfig.get("hyper-bot")
logger = hyperogger.Logger()
logger.set_level(config.log_level)


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

    async def _tool_call(self):
        pass

    async def event_handler(self, event: events.Event):
        data = json.dumps(event.data)
        logger.info(data)
        self.history.append({"role": "user", "content": data})
        resp = self._oai.chat.completions.create(
            model=self.model,
            messages=self.history,
            tools=self.tools,
            tool_choice="auto",
        )
        mess = resp.choices[0].message
        call = mess.tool_calls
        self.history.append(mess)
        logger.info(str(mess))
        logger.info(str(call))
        if call:
            for i in call:
                name = i.function.name
                params = json.loads(i.function.arguments)
                match name:
                    case "send_group_msg":
                        group_id = params.get("group_id")
                        raw_mess = params.get("message")
                        new_mess = []
                        for j in raw_mess:
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
                        new_mess = Message(*new_mess)
                        rs = await self.bot_api.send(group_id=group_id, message=new_mess)
                        time.sleep(3)
                    case _:
                        raise NotImplementedError
                self.history.append({"role": "tool", "tool_call_id": i.id, "name": i.function.name, "content": str(rs)})
            sed_resp = self._oai.chat.completions.create(
                model=self.model,
                messages=self.history,
            )
            fin_mess = sed_resp.choices[0].message
            self.history.append(fin_mess)
            logger.info(str(fin_mess))

    async def image_handler(self, url: str):
        raise NotImplementedError
