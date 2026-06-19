import hyperot.configurator
from cfgr.manager import BaseConfig


class AutoOther(BaseConfig):
    openai_endpoint: str
    openai_key: str
    openai_model: str
    moondream_key: str
    moondream_local: bool
    white: list



class BotConfig(BaseConfig):
    protocol: str = "OneBot"
    owner: list
    black_list: list
    silents: list
    connection: hyperot.configurator.BotHTTPC
    connection: hyperot.configurator.BotWSC
    connection: dict
    log_level: str = "INFO"
    log_use_nf: bool = False
    uin: int
    max_workers: int
    others: AutoOther

    def custom_post(self, **kwargs):
        if self.protocol == "OneBot":
            if self.connection["mode"] == "FWS":
                self.connection = hyperot.configurator.BotWSC(**self.connection)
            elif self.connection["mode"] == "HTTPC":
                self.connection = hyperot.configurator.BotHTTPC(**self.connection)
        elif self.protocol == "Kritor":
            self.connection = hyperot.configurator.BotWSC(**self.connection)


hyperot.configurator.BotConfig = BotConfig