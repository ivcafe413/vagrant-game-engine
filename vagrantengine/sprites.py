import logging
import os

import pygame
import pygame.image
import pygame.transform
import pygame.mask
from pygame import Vector2
from pygame.sprite import DirtySprite
from pyqtree import Index

from animators import SpriteAnimator

# from constants import ROOT_PATH

# IMAGES = os.path.join(ROOT_PATH, "assets", "images")
        
class MySprite(DirtySprite):
    def __init__(self, **kwargs):
        super().__init__()
        self.name = kwargs.get("name", self.__class__.__name__)

        self.images = None # type: list[pygame.Surface]
        self.animator = None # type: SpriteAnimator

        # Always account for possible keyword argument empty values (when possible)
        spritesheet = kwargs.get("spritesheet")
        image_file = kwargs.get("image_file")
        size = kwargs.get("size")

        if spritesheet is not None:
            self.images = slice_spritesheet(size, kwargs.get("images_path"), **spritesheet)
            self.image = self.images[kwargs.get("initial_slice", 0)]
            
        elif image_file is not None:
            # self.images = [kwargs.get("image", pygame.Surface((size, size)))]
            # self.image = self.images[0]
            image = pygame.image.load(os.path.join(kwargs.get("images_path"), image_file)).convert_alpha()
            # TODO: Scaled Height against set Width (size)
            image = pygame.transform.scale(image, (size, size))
            self.images = [image]
            self.image = image
            # self.mask = pygame.mask.from_surface(self.image)
        else:
            self.image = kwargs.get("image")
        
        self.mask = pygame.mask.from_surface(self.image)

        animations = kwargs.get("animations")
        if animations is not None:
            self.animator = SpriteAnimator(animations)
            # self.image = self.images[self.animator.current_slice]
        # else:
        #     self.image = self.images[0]

        self.rect = self.image.get_rect(x = kwargs.get("x", 0), y = kwargs.get("y", 0))
        self.last_rect = None # type: pygame.Rect

        # Game properties
        self.solid = kwargs.get("solid", False)

    # Sprite comes with an abstract update method, override
    def update(self, *args, **kwargs) -> None:
        # Single frame is passing. Can count internally for frame/anim changes
        self.last_rect = self.rect

        if self.animator is not None:
            self.animator.step()
            
            if self.animator.dirty:
                # Change in animation frame
                self.image = self.images[self.animator.current_slice]
                self.mask = pygame.mask.from_surface(self.image)
                self.dirty = 1
                self.animator.dirty = False

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

                if vertical_impact is None or abs(horizontal_impact) < abs(vertical_impact):
                    self.rect = self.rect.move(horizontal_impact, 0)
                elif horizontal_impact is None or abs(vertical_impact) < abs(horizontal_impact):
                    self.rect = self.rect.move(0, vertical_impact)
                index.insert(self, self.bbox)

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

    # This property is for use with pyqtree
    @property
    def bbox(self):
        return (self.rect.left, self.rect.top, self.rect.right, self.rect.bottom)

    @property
    def last_bbox(self):
        return (self.last_rect.left, self.last_rect.top, self.last_rect.right, self.last_rect.bottom)

    @property
    def is_moving(self):
        return self.rect != self.last_rect

class Actor(MySprite):
    def __init__(self, images_path, **kwargs):
        super().__init__(images_path, **kwargs)

        self.is_player = kwargs.get("player_character", False)

        self.movement_vector = (0, 0) # init, not moving
        self.speed = 5

    def apply_movement_vector(self, x, y):
        """Build a movement vector for the actor.
        Is additive, can be called multiple times.
        Actor.update processes the move."""
        dx = self.movement_vector[0] + (x * self.speed)
        dy = self.movement_vector[1] + (y * self.speed)
        self.movement_vector = (dx, dy)

    def update(self, *args, **kwargs) -> None:
        super().update(*args, **kwargs)
        if any(v != 0 for v in self.movement_vector):
            self.rect = self.rect.move(self.movement_vector)
            self.dirty = 1

    # def resolve_collision(self, collider: MySprite, index: Index):
    #     """"""
    #     if collider.solid:
    #         # 
    #         # If it's solid, bump 'myself' away
    #         index.remove(self, self.bbox)
    #         # Reset my position
    #         self.rect = self.last_rect
    #         index.insert(self, self.bbox)

class Tile(MySprite):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

def slice_spritesheet(size: int, images_path: str, file: str, slice_specs, slices: list) -> list[pygame.Surface]:
    """file, frame_size, frames"""
    images = [] # type: list[pygame.Surface]

    image = pygame.image.load(os.path.join(images_path, file)).convert_alpha()
    # pygame.image.save(image, os.path.join(SPRITESHEETS, "temp.png"))

    # Scale frame size to tile size (by width)
    delta = size / slice_specs["w"]
    scaled_height = round(slice_specs["h"] * delta)

    for y in range(slices[1]):
        for x in range(slices[0]):
            s = pygame.Surface((slice_specs["w"], slice_specs["h"])).convert_alpha()
            s.fill((0, 0, 0, 0)) # IMPORTANT: need to set default background to transparent
            s.blit(
                image, # source
                (0, 0), # dest
                pygame.Rect # area
                (
                    slice_specs["spacing"] + (2 * x * slice_specs["spacing"]) + (x * slice_specs["w"]),
                    slice_specs["spacing"] + (2 * y * slice_specs["spacing"]) + (y * slice_specs["h"]),
                    slice_specs["w"], slice_specs["h"]
                )
            )
            # pygame.image.save(frame, os.path.join(SPRITESHEETS, f"non_scaled_{x}_{y}.png"))
            s = pygame.transform.scale(s, (size, scaled_height))
            images.append(s)
    return images