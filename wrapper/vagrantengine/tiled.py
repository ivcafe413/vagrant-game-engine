import logging
import os
from typing import Any

import pygame

class TiledType:
    def __init__(self, name: str, props: list):
        self.name = name
        self.additional_properties = dict() # type: dict[str, Any]
        for p in props:
            prop_name = p.get("name")
            self.additional_properties[prop_name] = p.get("value")

class TiledObject:
    def __init__(self, id: int, name: str, tiledtype: TiledType, x: float, y: float, width: float, height: float, **kwargs):
        """Convert Dict to Concrete Object for Code purposes"""
        self.id = id
        self.name = name
        
        self.rect = pygame.Rect(x, y, width, height)
        self.type = tiledtype

        self.gid = kwargs.get("gid")