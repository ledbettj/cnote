import cnote


class SimpleWindow(cnote.NotificationWindow):
    colors = {
        'background': (.74, 0.80, 0.85, 1.0),
        'title': (1.0, 1.0, 1.0, 1.0),
        'body': (1.0, 1.0, 1.0, 1.0),
        'shadow-urgency-0': (0.0, 0.0, 0.0, 1.0),
        'shadow-urgency-1': (0.0, 0.0, 0.0, 1.0),
        'shadow-urgency-2': (0.6, 0.0, 0.0, 1.0)
        }

    SHADOW_BLUR = 0
    SHADOW_WIDTH = 0
    CORNER_RADIUS = 0

    PADDING = 0

    def __init__(self, n):
        super(SimpleWindow, self).__init__(n)
        self.regenerate()
