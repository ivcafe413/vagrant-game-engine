import logging
import os

import pygame
import pygame.image
import pygame.transform
import pygame.mask
from pygame import Vector2
from pygame.sprite import DirtySprite
from pyqtree import Index

from .animators import SpriteAnimator
from .tiled import TiledType

# New Set of Classes around re-vamped TileMap loading system
class TilemapSprite(DirtySprite):
    def __init__(self, tilemap: pygame.Surface, **kwargs):
        super().__init__()

        self.image = tilemap
        self.rect = tilemap.get_rect()

class GameSprite(DirtySprite):
    def __init__(self, x, y, width, height, image=None, **kwargs):
        super().__init__()

        self.name = kwargs.get("name", self.__class__.__name__)
        self.type = kwargs.get("type") # type: TiledType
        # self.rect = pygame.Rect(kwargs.get("x"), kwargs.get("y"), kwargs.get("width"), kwargs.get("height"))
        self.rect = pygame.Rect(x, y, width, height)
        if image is None:
            self.image = pygame.Surface((width, height)).convert_alpha()
            self.image.fill((0, 0, 0, 0))
        else:
            self.image = image

        self.last_rect = None # type: pygame.Rect
        if self.image is not None:
            self.mask = pygame.mask.from_surface(self.image)

        # self.images = None # type: list[pygame.Surface]
        # self.animator = None # type: SpriteAnimator

        # Sprite comes with an abstract update method, override
    def update(self, *args, **kwargs) -> None:
        # Single frame is passing. Can count internally for frame/anim changes
        self.last_rect = self.rect

    @property
    def x(self):
        return self.rect.x

    @property
    def center(self):
        return self.rect.center

    @property
    def left(self):
        return self.rect.left

    @property
    def right(self):
        return self.rect.right

    @property
    def y(self):
        return self.rect.y

    @property
    def top(self):
        return self.rect.top

    @property
    def bottom(self):
        return self.rect.bottom

    # These properteis are for use with pyqtree, movement/collision detection
    @property
    def bbox(self):
        return (self.rect.left, self.rect.top, self.rect.right, self.rect.bottom)

    @property
    def last_bbox(self):
        return (self.last_rect.left, self.last_rect.top, self.last_rect.right, self.last_rect.bottom)

    @property
    def is_moving(self):
        return self.rect != self.last_rect

class AnimatedSprite(GameSprite):
    def __init__(self, images: list[pygame.Surface], animations, **kwargs):
        super().__init__(**kwargs)

        self.images = images
        self.animator = SpriteAnimator(animations)

    def update(self, *args, **kwargs) -> None:
        super().update(args, kwargs)
        self.animator.step()
            
        if self.animator.dirty:
            # Change in animation frame
            self.image = self.images[self.animator.current_slice]
            self.mask = pygame.mask.from_surface(self.image)
            self.dirty = 1
            self.animator.dirty = False

class MoveableSprite(GameSprite):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.movement_vector = (0, 0) # init, not moving
        self.speed = 5

    def apply_movement_vector(self, x, y):
        """Build a movement vector for the actor.
        Is additive, can be called multiple times.
        Actor.update processes the move."""
        dx = self.movement_vector[0] + (x * self.speed)
        dy = self.movement_vector[1] + (y * self.speed)
        self.movement_vector = (dx, dy)

    def resolve_collisions(self, index: Index):
        collisions = (o for o in index.intersect(self.bbox) if o != self)

        # for o in index.intersect(self.bbox) if o != self:

        # TODO: Build Priority Index for movers/resolution
        for c in collisions:
            if c.solid:
                logging.info(f"{self.name} colliding with {c.name}")
                index.remove(self, self.bbox)
                # Calculate 'impact'
                # 'Impact' is how much into the target the mover has impacted
                # Calculate by checking solid boundaries - (minus) mover boundaries
                # Ex: What is bigger? Solid right - mover right, or solid bottom - mover bottom

                # Calculate which cardinal direction the mover is from the solid
                cardinal = Vector2(self.center) - Vector2(c.center)
                # Step 2: Simplify situations in which mover is only in one direction
                if cardinal.x < 0:
                    horizontal_impact = c.left - self.right
                elif cardinal.x > 0:
                    horizontal_impact = c.right - self.left
                else: horizontal_impact = None
                logging.info(f"Horizontal Impact: {horizontal_impact}")

                if cardinal.y < 0:
                    vertical_impact = c.top - self.bottom
                elif cardinal.y > 0:
                    vertical_impact = c.bottom - self.top
                else: vertical_impact = None
                logging.info(f"Vertical Impact: {vertical_impact}")

                if vertical_impact is None or (horizontal_impact is not None and abs(horizontal_impact) < abs(vertical_impact)):
                    self.rect = self.rect.move(horizontal_impact, 0)
                elif horizontal_impact is None or (vertical_impact is not None and abs(vertical_impact) < abs(horizontal_impact)):
                    self.rect = self.rect.move(0, vertical_impact)
                index.insert(self, self.bbox)

    def update(self, *args, **kwargs) -> None:
        super().update(*args, **kwargs)
        if any(v != 0 for v in self.movement_vector):
            self.rect = self.rect.move(self.movement_vector)
            self.dirty = 1

class ActorSprite(MoveableSprite, AnimatedSprite):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

#     # Sprite comes with an abstract update method, override
#     def update(self, *args, **kwargs) -> None:
#         # Single frame is passing. Can count internally for frame/anim changes
#         self.last_rect = self.rect

#         if self.animator is not None:
#             self.animator.step()
            
#             if self.animator.dirty:
#                 # Change in animation frame
#                 self.image = self.images[self.animator.current_slice]
#                 self.mask = pygame.mask.from_surface(self.image)
#                 self.dirty = 1
#                 self.animator.dirty = False
