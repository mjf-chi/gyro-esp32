### A leaf requires attention
### once given attention it will be satisfied for a certain amount of time
### the goal is to keep the leaf satisfied
import math


class Leaf:

    HAPPY = 'Happy'
    BORED = 'Bored'
    UPSET = 'Upset'

    BASE_TTL = 45
    BORED_THRESHOLD = math.floor(BASE_TTL * (2/3))
    UPSET_THRESHOLD = math.floor(BASE_TTL * (1/3))

    def __init__(self, hasAttention, leds):
        print('Initializing Leaf')
        ### Requires an attention test function
        self._hasAttention = hasAttention
        self._leds = leds
        self._life = self.BASE_TTL
        self._mentalState = self.HAPPY


    # @property
    # def hasAttention(self):
    #     return self._hasAttention()

    @property
    def life(self):
        return self._life

    @life.setter
    def life(self, new_life):
        self._life = new_life

    ### Called from parents loop
    def update(self):
        isAttention = self._hasAttention()

        if isAttention and self.life != self.BASE_TTL:
            self.life = self.BASE_TTL
            self._mentalState = self.HAPPY
            print('Reset life')
        else:
            self.life -= 1

            if self.life == self.BORED_THRESHOLD:
                self._mentalState = self.BORED
            elif self.life == self.UPSET_THRESHOLD:
                self._mentalState = self.UPSET

        self.show()


    ## Update leds
    def show(self):
        if self._mentalState == self.HAPPY:
            print('Happy - ', self._life)
            self._leds.fill((0, 255, 0))
        elif self._mentalState == self.BORED:
            print('Bored', self._life)
            self._leds.fill((255, 255, 0))
        elif self._mentalState == self.UPSET:
            print('Upset', self._life)
            self._leds.fill((255, 0, 0))

        self._leds.write()
