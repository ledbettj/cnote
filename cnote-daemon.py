#!/usr/bin/env python
import gtk
import dbus.mainloop.glib
import cnote
import logging
import optparse
import os

# acceptable arguments to --debug-level
debug_levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
    }

# acceptable arguments to --window-type
window_types = {
    'default': cnote.NotificationWindow,
    'ubuntu': cnote.UbuntuWindow
}

parser = optparse.OptionParser()

parser.add_option("-r", "--replace", action="store_true", default=False,
                  dest="replace",
                  help="stop other notification services prior to starting.")

parser.add_option("-d", "--debug-level", type="choice", dest="debug_level",
                  default="warning", choices=[k for k in debug_levels],
                  help="level of debugging information to print to stderr: "
                  "'debug,' 'info,' 'warning' (default), 'error,' or"
                  " 'critical.'")

parser.add_option("-w", "--window-type", type="choice", dest="window_type",
                  default="default", choices=[k for k in window_types],
                  help="notification style: one of 'default,' or 'ubuntu.'")

(opts, args) = parser.parse_args()

if opts.replace:
    os.system("killall notify-osd ; killall notification-daemon")

logging.basicConfig(level=debug_levels[opts.debug_level])
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

logging.info("starting dbus service")
manager = cnote.NotificationManager(window_types[opts.window_type])
service = cnote.NotificationService(manager)

gtk.main()
