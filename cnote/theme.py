import simplejson as json
import os
import logging


class ThemeManager:

    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.themes = {}
        self.load_themes()

    def load_themes(self):
        for root, dirs, files in os.walk(self.base_dir):
            file_list = [os.path.join(root, f) for f in files
                         if f.endswith('.cnote-theme')]
            for f in file_list:
                theme = Theme(f)
                self.themes[theme['name']] = theme
        self.resolve_bases()

    def resolve_bases(self):
        for theme_name in self.themes:
            logging.debug(theme_name)
            theme = self.themes[theme_name]
            if theme.get('override') != None:
                theme.set_base(self.themes[theme['override']])

    def get_theme(self, name):
        return self.themes[name]

    def list_themes(self):
        return [t for t in self.themes]


class Theme:

    def __init__(self, filename):
        self.settings = {}
        self.filename = filename
        self.base = None
        self.load()

    def get(self, k):
        if k in self.settings:
            return self.settings[k]
        elif self.base != None:
            return self.base.get(k)
        else:
            return None

    def set(self, k, v):
        self.settings[k] = v

    def save(self):
        f = open(self.filename, 'w')
        json.dump(self.settings, f, sort_keys=True, ident=' ' * 4)
        f.close()

    def load(self):
        f = open(self.filename, 'r')
        self.settings = json.load(f)
        f.close()

    def __getitem__(self, index):
        return self.get(index)

    def __setitem__(self, key, value):
        self.set(key, value)

    def set_base(self, parent):
        self.base = parent
