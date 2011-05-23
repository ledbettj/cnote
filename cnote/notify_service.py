import dbus.service

# instead of typing these over and over again...
DBUS_BUS_NAME = 'org.freedesktop.Notifications'
DBUS_OBJ_PATH = '/org/freedesktop/Notifications'


class Notification:

    # reasons a notification might have been closed
    CLOSED_EXPIRED   = 1
    CLOSED_DISMISSED = 2
    CLOSED_REQUESTED = 3
    CLOSED_UNKNOWN   = 4

    # bounds for a notification to stay on the screen (ms)
    MIN_TIMEOUT = 7000
    MAX_TIMEOUT = 15000
    DEFAULT_TIMEOUT = 8000

    # if no urgency is specified, assume normal urgency
    DEFAULT_URGENCY = 1

    # if no location is specified, let the window choose it's position
    DEFAULT_LOCATION = (-1, -1)

    def __init__(self, nid, name, icon, summary, body, actions, hints,
                 timeout):
        self.nid = int(nid)
        self.name = name
        self.icon = icon
        self.summary = summary
        self.body = body
        self.actions = []
        for value, localized in zip(actions[0::2], actions[1::2]):
            self.actions.append((str(value), str(localized)))
        self.hints = hints

        # default values for hints
        self.urgency = self.DEFAULT_URGENCY
        self.timeout = self.DEFAULT_TIMEOUT
        self.category = None
        self.resident = False
        self.location = self.DEFAULT_LOCATION

        # unpack any hints we might handle
        if 'urgency' in hints:
            self.urgency = int(hints['urgency'])
        if 'category' in hints:
            self.category = str(hints['category'])
        if 'resident' in hints:
            self.resident = bool(hints['resident'])
        if 'x' in hints and 'y' in hints:
            self.location = (int(hints['x']), int(hints['y']))

        # the spec says a timeout of 0 means no timeout --
        # but isn't that what the 'resident' hint is for?
        if timeout in [-1, 0]:
            self.timeout = self.DEFAULT_TIMEOUT
        elif timeout < self.MIN_TIMEOUT:
            self.timeout = self.MIN_TIMEOUT
        elif timeout > self.MAX_TIMEOUT:
            self.timeout = self.MAX_TIMEOUT

    def set_id(self, nid):
        self.nid = nid

    def get_id(self):
        return self.nid

    def __format__(self, format_spec):
        result = "Notification-{0} {{\n".format(self.get_id())
        for k in self.__dict__:
            if k == "hints":
                result += "\thints: '{0}'\n".format(
                    ', '.join([key for key in self.hints]))
            else:
                result += "\t{0}: '{1}'\n".format(k, self.__dict__[k])
        return result + "}"


class NotificationService(dbus.service.Object):
    """
    Implements the Desktop Notifications Specification D-BUS service,
    version 1.2.

    See:
    people.gnome.org/~mccann/docs/notification-spec/notification-spec-1.2.html
    """

    def __init__(self, manager):
        bus_name = dbus.service.BusName(DBUS_BUS_NAME,
                                        bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name,
                                     DBUS_OBJ_PATH)
        self.mgr = manager
        self.mgr.set_service(self)

    # D-BUS methods required by the spec
    @dbus.service.method(DBUS_BUS_NAME,
                         in_signature='susssasa{sv}i',
                         out_signature='u')
    def Notify(self, name, n_id, icon, summary, body, actions, hints, timeout):
        n = Notification(n_id, name, icon, summary, body, actions, hints,
                         timeout)
        if n_id == 0:
            return self.mgr.new(n)
        else:
            return self.mgr.update(n)

    @dbus.service.method(DBUS_BUS_NAME,
                         in_signature='',
                         out_signature='as')
    def GetCapabilities(self):
        return self.mgr.get_capabilities()

    @dbus.service.method(DBUS_BUS_NAME,
                         in_signature='u',
                         out_signature='')
    def CloseNotification(self, nid):
        self.mgr.close(nid, Notification.CLOSED_REQUESTED)

    @dbus.service.method(DBUS_BUS_NAME,
                         in_signature='',
                         out_signature='ssss')
    def GetServerInformation(self):
        return self.mgr.get_server_information()

    # D-BUS signals required by the spec
    @dbus.service.signal(DBUS_BUS_NAME, signature='uu')
    def NotificationClosed(self, nid, reason):
        pass

    @dbus.service.signal(DBUS_BUS_NAME, signature='us')
    def ActionInvoked(self, nid, action_key):
        pass
