#!/usr/bin/env python
import gtk
import dbus.mainloop.glib
import cnote
import logging
import optparse
import os
import xdg.BaseDirectory

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

# where to find themes, in order of preference
theme_dirs = [
    os.path.join(xdg.BaseDirectory.xdg_data_home, 'cnote', 'themes'),
    '/usr/share/cnote/themes',
    '/usr/local/share/cnote/themes',
    './themes'
    ]

themes = cnote.ThemeManager(theme_dirs)
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

(opts, args) = parser.parse_args()

if opts.replace:
    os.system("killall notify-osd ; killall notification-daemon")

logging.getLogger().setLevel(debug_levels[opts.debug_level])
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

logging.info("starting dbus service")
manager = cnote.NotificationManager(themes.get_theme(opts.theme))
service = cnote.NotificationService(manager)

gtk.main()
