import cnote
import logging


class UbuntuWindow(cnote.NotificationWindow):

    colors = {
        'background': (0.074, 0.074, 0.074, 0.875),
        'title': (1.0, 1.0, 1.0, 1.0),
        'body': (0.914, 0.914, 0.914, 1.0),
        'shadow-urgency-0': (0.0, 0.0, 0.0, 1.0),
        'shadow-urgency-1': (0.0, 0.0, 0.0, 1.0),
        'shadow-urgency-2': (0.0, 0.0, 0.0, 1.0)
        }

    SHADOW_BLUR = 12
    SHADOW_WIDTH = 1

    def __init__(self, n):
        super(UbuntuWindow, self).__init__(n)
