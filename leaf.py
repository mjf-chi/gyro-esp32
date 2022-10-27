### A leaf requires attention
### once given attention it will be satisfied for a certain amount of time
### the goal is to keep the leaf satisfied
import math


class Leaf:

    HAPPY = 'Happy'
    BORED = 'Bored'
    UPSET = 'Upset'

    BASE_TTL = 30
    BORED_THRESHOLD = math.floor(BASE_TTL * (2/3))
    UPSET_THRESHOLD = math.floor(BASE_TTL * (1/3))

    def __init__(self, hasAttention, leds):
        ### Requires an attention test function
        self._hasAttention = hasAttention
        self._leds = leds
        self._life = BASE_TTL
        self._mentalState = HAPPY


    @property
    def hasAttention(self):
        return self._hasAttention()

    @property
    def life(self):
        return self._life

    @life.setter(self, new_life):
        self._life = new_life

    ### Called from parents loop
    def update():
        if self.hasAttention && self.life != BASE_TTL
            self.life = BASE_TTL
            self._mentalState = HAPPY
        else
            self.life -= 1

            if self.life == BORED_THRESHOLD
                self._mentalState = BORED
            elif self.life == UPSET_THRESHOLD
                self._mentalState = UPSET

        self.show()

    ## Update leds
    def show():
        if self._mentalState == HAPPY
            self._leds.fill((0, 255, 0))
        elif self._mentalState == BORED
            self._leds.fill((255, 255, 0))
        elif self._mentalState == UPSET
            self._leds.fill((255, 0, 0))

        self._leds.write()
