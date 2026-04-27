from config import *

class Tracker:
    def __init__(self):
        self.cx = FRAME_WIDTH // 2
        self.cy = FRAME_HEIGHT // 2

    def compute(self, x, y):
        dx = x - self.cx
        dy = y - self.cy

        if abs(dx) < DEAD_ZONE:
            dx = 0
        if abs(dy) < DEAD_ZONE:
            dy = 0

        return dx, dy
