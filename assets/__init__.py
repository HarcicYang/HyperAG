from dataclasses import dataclass, field
import os

@dataclass
class Resource:
    all: list = field(default_factory=list)


def resource(cls: type):
    c = cls()
    c.all = list(vars(cls()).keys())
    c.all.remove("all")
    return c


@resource
@dataclass
class Face(Resource):
    JAVA_AHA_CONFUSED: str = os.path.abspath("assets/" + "java_aha_confused.png")
    KIANA_EATING: str = os.path.abspath("assets/" + "kiana_eating.png")
    SAKURABA_CONFUSED: str = os.path.abspath("assets/" + "sakuraba_confused.png")
    SAKURABA_HOMO: str = os.path.abspath("assets/" + "sakuraba_homo.png")
    TERIRI_CUTE: str = os.path.abspath("assets/" + "teriri_cute.png")
    TERIRI_WISDOM_1: str = os.path.abspath("assets/" + "teriri_wisdom_1.png")
    TERIRI_WISDOM_2: str = os.path.abspath("assets/" + "teriri_wisdom_2.png")
    VV_GENE: str = os.path.abspath("assets/" + "vv_gene.png")
    VV_STOP: str = os.path.abspath("assets/" + "vv_stop.png")
