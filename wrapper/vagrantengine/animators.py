import logging
import bisect

class Animation:
    def __init__(self, slices: list, durations: list):
        """Creates a single animation instance.
        Functionality in this class is geared towards running
        this individual animation."""
        # Check matching length on slice list and duration list
        if len(slices) != len(durations):
            raise ValueError("Lengths of slices and durations need to be equal.")
        self.slices = slices
        self.slice_frames = []
        self.paused = False

        # Set up frame counts
        frame_counter = 0
        for d in durations:
            frame_counter += d
            self.slice_frames.append(frame_counter)

class SpriteAnimator:
    def __init__(self, animations: dict):
        """Takes a dictionary of animations and builds functionality around
        them to play, stop, load and track animation frames for a sprite."""
        self.animations = {k:Animation(**v) for (k, v) in animations.items()}
        self.reverse_lookup = {v:k for k, v in self.animations.items()}
        
        self.current_animation = None # type: str
        # self.default_animation = Animation(animations[initial_animation])
        # self.default_animation.paused = True
        self.stack = [] # type: list[Animation]

        self.frame_count = 0
        # self.current_index = left_search(self.current.slice_frames, self.frame_count)
        self.current_index = 0

        # self.threshold = self.current.slice_frames[self.current_index]
        self.threshold = 0
        # self.current_slice = self.current.slices[self.current_index]
        self.current_slice = 0

        self.dirty = False

    @property
    def current(self):
        try:
            return self.stack[-1]
        except IndexError:
            return None

    def step(self):
        if (self.current is not None) and (not self.current.paused):
            self.frame_count += 1

            if self.frame_count > self.threshold:
                # Move to next frame
                self.current_index += 1
                # Loop around at the end
                if self.current_index >= len(self.current.slice_frames):
                    self.frame_count = 0
                    self.current_index = 0

                self.threshold = self.current.slice_frames[self.current_index]
                self.current_slice = self.current.slices[self.current_index]
                self.dirty = True

    def start(self, action: str):
        """Add a new animation to the stack.
        Top of the stack should be the playing animation."""
        # try:
        #     self.stack.remove(self.animations[action])
        # except ValueError:
        #     pass
        self.current_animation = action
        self.stack.append(self.animations[action])

        # self.frame_count = initial_frame
        # self.frame_count = 0
        # self.current_index = left_search(self.current.slice_frames, self.frame_count)
        # Start on the second frame/slice
        self.current_index = 1
        self.threshold = self.current.slice_frames[self.current_index]
        self.frame_count = self.current.slice_frames[0] + 1

        self.current_slice = self.current.slices[self.current_index]

        self.dirty = True

    def stop(self, action: str):
        # Pop last instance of this action off the animation stack
        self.stack.reverse()
        try:
            self.stack.remove(self.animations[action])
        except ValueError:
            pass
        self.stack.reverse()

        # If we're stopping the last animation in the stack
        if self.current is None:
            last_animation = self.animations[action]
            # logging.info(f"Last Animation: {action}")
            self.current_animation = None
            self.current_index = 0
            self.threshold = 0
            self.frame_count = 0
            self.current_slice = last_animation.slices[self.current_index]
        else:
            self.current_animation = self.reverse_lookup[self.current]

            # self.current_index = left_search(self.current.slice_frames, self.frame_count)
            # self.threshold = self.current.slice_frames[self.current_index]
            
            # Start on the second frame/slice
            self.current_index = 1
            self.threshold = self.current.slice_frames[self.current_index]
            self.frame_count = self.current.slice_frames[0] + 1
            self.current_slice = self.current.slices[self.current_index]

        self.dirty = True

def left_search(nums, item):
    # From https://stackoverflow.com/questions/39358092/range-as-dictionary-key-in-python
    # adjust, as bisect returns not exactly what we want
    i = bisect.bisect_left(nums, item)
    # if i == len(nums) or nums[i] != item:
    #     i -= 1

    return i