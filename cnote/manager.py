import logging
import cnote


class NotificationManager:
    def __init__(self, themes):
        self.next_id = 1
        self.srv = None
        self.notifications = {}
        self.pending = []
        self.themes = themes

    def get_server_information(self):
        return ('cnote notification server',
                '0.1',
                'John Ledbetter <john.ledbetter@gmail.com>',
                '1.2.')

    def get_capabilities(self):
        return ['body', 'icon-static']

    def new(self, n):
        nid = self.next_id
        self.next_id += 1
        n.set_id(nid)

        logging.debug('new {0}'.format(n))

        self.notifications[nid] = cnote.NotificationWindow(
            n, self.themes.get_active())

        self.pending.append(nid)
        if len(self.pending) == 1:
            self.show_next_notification()

        return nid

    def update(self, n):
        nid = n.get_id()
        if not nid in self.notifications:
            logging.warn("application '{0}' requested bad ID '{1}'".format(
                    n.name, nid))
            return 0
        else:
            logging.debug('update notification {0}'.format(n))
            self.notifications[nid].update_from(n)

        return nid

    def close(self, nid, reason):
        logging.debug("request notification-{0} close (reason {1})".format(
                nid, reason))
        self.notifications[nid].close(reason)

    def set_service(self, srv):
        self.srv = srv

    def show_next_notification(self):
        if len(self.pending) != 0:
            nid = self.pending[0]
            n = self.notifications[nid]
            n.on_close(self.on_notification_close, self)
            n.show()

    def on_notification_close(self, nid, reason):
        logging.debug('notification-{0} closed (reason {1})'.format(
                nid, reason))
        self.notifications[nid] = None
        self.pending.remove(nid)
        self.srv.NotificationClosed(nid, reason)
        self.show_next_notification()

    def select_theme(self, theme_name):
        self.themes.select_theme(theme_name)
