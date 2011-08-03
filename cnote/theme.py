import simplejson as json
import os
import logging
import xdg.BaseDirectory
import inotifyx
import glib


class ThemeManager:

    DEFAULT_DIRS = [
        os.path.join(xdg.BaseDirectory.xdg_data_home, 'cnote', 'themes'),
        '/usr/share/cnote/themes',
        '/usr/local/share/cnote/themes',
        './themes'
        ]

    def __init__(self, base_dirs=DEFAULT_DIRS):
        self.base_dirs = base_dirs
        self.themes = {}
        self.load_themes()
        self.watches = {}
        self.watch_fd = None
        self.install_watcher()
        self.active = None

    def select_theme(self, name):
        if name in self.themes:
            self.active = name

    def get_active(self):
        return self.themes[self.active]

    def load_themes(self):
        for base_dir in self.base_dirs:
            for root, dirs, files in os.walk(base_dir):
                file_list = [os.path.join(root, f) for f in files
                             if f.endswith('.cnote-theme')]
                for f in file_list:
                    theme = Theme(f)
                    if not theme.success:
                        continue
                    theme_name = theme['metadata']['name']
                    if theme_name not in self.themes:
                        self.themes[theme_name] = theme
                    else:
                        logging.warning(
                            "ignoring duplicate theme {0}".format(theme_name))
        self.resolve_bases()

    def install_watcher(self):
        self.watch_fd = inotifyx.init()
        for d in self.base_dirs:
            if os.path.isdir(d):
                logging.info('adding watch for {0}'.format(d))
                self.watches[inotifyx.add_watch(self.watch_fd, d,
                                                inotifyx.IN_MODIFY |
                                                inotifyx.IN_CREATE)] = d

        glib.timeout_add_seconds(3, self.do_watch)

    def do_watch(self):
        events = inotifyx.get_events(self.watch_fd, 0)
        if events != None:
            filt = [e for e in events if (not e.name.startswith('.') and
                                          e.name.endswith('.cnote-theme'))]
            for e in filt:
                path = os.path.join(self.watches[e.wd], e.name)
                logging.info('reloading: {0}: {1}'.format(
                        path, e.get_mask_description()))
                t = Theme(path)
                if not t.success:
                    continue
                tname = t['metadata']['name']
                self.themes[tname] = t
                self.resolve_bases()

        return 1

    def resolve_bases(self):
        for theme_name in self.themes:
            logging.debug(theme_name)
            theme = self.themes[theme_name]
            if 'override' in theme:
                base_name = theme['override']
                if base_name in self.themes:
                    theme.set_base(self.themes[theme['override']])
                else:
                    logging.error('theme {0} overrides {1},'
                                  ' but {1} not found'.format(theme_name,
                                                              base_name))

    def get_theme(self, name):
        return self.themes[name]

    def list_themes(self):
        return [t for t in self.themes]


class Theme:

    def __init__(self, filename):
        self.data = {}
        self.filename = filename
        self.base = None
        self.success = False
        self.load()

    def value(self, *args):
        info = self['metadata']['name'] + ':/' + '/'.join(args)

        item = self.data
        for a in args:
            if a in item:
                item = item[a]
            else:
                if self.base:
                    logging.debug('using parent for ' + info)
                    return self.base.value(*args)
                else:
                    raise KeyError(info)

        return item

    def save(self):
        f = open(self.filename, 'w')
        json.dump(self.data, f, sort_keys=True, ident=' ' * 4)
        f.close()

    def load(self):
        f = open(self.filename, 'r')

        try:
            self.data = json.load(f)
            self.success = True
        except json.JSONDecodeError as err:
            logging.error("failed to load theme from {0}: {1}".format(
                    self.filename, err))

        f.close()

    def __getitem__(self, index):
        return self.data[index]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, key):
        return key in self.data or (self.base != None and key in self.base)

    def set_base(self, parent):
        self.base = parent
