#!/usr/bin/env python
import gtk
import dbus.mainloop.glib
import cnote
import logging
import optparse
import os
import xdg.BaseDirectory
import sys


# configure logging to log warnings/errors until the --debug-level is parsed,
# in case things go wrong during theme loading
logging.basicConfig(level=logging.WARNING,
                    format='%(asctime)s: %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %I:%M:%S %p',
                    filename=os.path.join(xdg.BaseDirectory.xdg_cache_home,
                                          'cnote.log'))

# acceptable arguments to --debug-level
debug_levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    }

themes = cnote.ThemeManager()
parser = optparse.OptionParser()

parser.add_option("-r", "--replace", action="store_true", default=False,
                  dest="replace",
                  help="stop other notification services prior to starting.")

parser.add_option("-d", "--debug-level", type="choice", dest="debug_level",
                  default="warning", choices=[k for k in debug_levels],
                  help="level of debugging information to print to stderr: "
                  "'debug,' 'info,' 'warning' (default), or 'error.'")

parser.add_option("-t", "--theme", type="choice", dest="theme",
                  default="default", choices=themes.list_themes(),
                  help="notification theme")

parser.add_option("-l", "--list-themes", action="store_true", default=False,
                  dest="list_themes",
                  help="list available cnote themes and exit.")

(opts, args) = parser.parse_args()

if opts.list_themes:
    items = themes.list_themes()
    items.sort()
    for tn in items:
        t = themes.get_theme(tn)
        print("* {0}-{2}\n"
              "    author: {1}\n"
              "    info:   {3}\n".format(tn,
                                         t.value('metadata', 'author'),
                                         t.value('metadata', 'version'),
                                         t.value('metadata', 'description')))
    sys.exit(0)

if opts.replace:
    os.system("killall notify-osd ; killall notification-daemon")

logging.getLogger().setLevel(debug_levels[opts.debug_level])
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

logging.info("starting dbus service")
try:
    themes.select_theme(opts.theme)
    manager = cnote.NotificationManager(themes)
    service = cnote.NotificationService(manager)
    gtk.main()
except dbus.DBusException as ex:
    logging.error(ex)
    print ex
