import gtk
import glib
import cnote
import cairo
import pango
import pangocairo
import logging


class NotificationWindow(gtk.Window):

    __gsignals__ = {
        'expose-event' : 'override'
        }

    def __init__(self, n, theme):
        super(NotificationWindow, self).__init__()

        self.t = theme

        self.n = n
        self.fix_timeout()

        self.close_cb = None
        self.close_arg = None
        self.timer = 0

        self.set_property('skip-taskbar-hint', True)
        self.set_property('accept-focus', False)
        self.set_keep_above(True)
        self.set_app_paintable(True)
        self.set_decorated(False)
        self.set_size_request(1, 1)

        screen = self.get_screen()
        argbmap = screen.get_rgba_colormap()

        root = gtk.gdk.screen_get_default()
        if root.supports_net_wm_hint('_NET_WORKAREA'):
            prop = root.get_root_window().property_get('_NET_WORKAREA')
            self.root = {
                'x': prop[2][0],
                'y': prop[2][1],
                'w': prop[2][2],
                'h': prop[2][3]
                }
        else:
            self.root = {
                'x': 0,
                'y': 0,
                'w': gtk.gdk.screen_width(),
                'h': gtk.gdk.screen_height()
                }

        logging.debug("root window x:{0}->{1}, y:{2}->{3}".format(
                self.root['x'], self.root['w'],
                self.root['y'], self.root['h']))

        if argbmap is not None:
            self.set_colormap(argbmap)
        else:
            logging.warn("no alpha channel available")

        self.image = None

        self.surface = None

        self.regenerate()

    def fix_timeout(self):
        timeout = self.n.timeout
        # the spec says a timeout of 0 means no timeout --
        # but isn't that what the 'resident' hint is for?
        if timeout in [-1, 0]:
            timeout = self.t.value('timeout', 'default')
        elif timeout < self.t.value('timeout', 'minimum'):
            timeout = self.t.value('timeout', 'minimum')
        elif timeout > self.t.value('timeout', 'maximum'):
            timeout = self.t.value('timeout', 'maximum')

        self.n.timeout = timeout

    def update_from(self, n):
        self.n = n
        self.fix_timeout()
        self.regenerate()
        # only perform the following if we already started the timer
        if self.timer != 0:
            self.queue_draw()
            self.start_timer()

    def close(self, reason):
        if self.close_cb:
            self.close_cb(self.n.get_id(), reason)
            self.destroy()
        return False

    def on_close(self, callback, arg):
        self.close_cb = callback
        self.close_arg = arg

    def start_timer(self):
        if self.n.resident:
            return

        self.stop_timer()
        self.timer = glib.timeout_add_seconds(
            self.n.timeout / 1000,
            self.close,
            cnote.Notification.CLOSED_EXPIRED)

    def stop_timer(self):
        if self.timer != 0:
            glib.source_remove(self.timer)
            self.timer = 0

    def show(self):
        self.start_timer()
        super(NotificationWindow, self).show()

    def do_expose_event(self, arg):

        # allow notifications to be 'click through'
        if self.t.value('miscellaneous', 'click-through'):
            self.window.input_shape_combine_region(gtk.gdk.Region(), 0, 0)
            logging.debug('setting empty region as our region')

        cr = self.window.cairo_create()
        cr.rectangle(arg.area.x, arg.area.y, arg.area.width, arg.area.height)
        cr.clip()

        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_surface(self.surface)
        cr.paint()

    def regenerate(self):
        # padding is the transparent space around the notification, which
        # the blurred shadow will bleed into
        padding = self.t.value('dimensions', 'padding')
        if self.t.value('image', 'visible'):
            self.try_load_image()
        # dimensions of the notification
        width, height = self.resize_window_as_needed(padding)
        # dimensions of the window (e.g. including padding)
        win_width = 2 * padding + width
        win_height = 2 * padding + height

        # if no location was specified, do our own thing
        logging.debug('figuring out location')
        location = self.n.location
        if location[0] == -1 or self.t.value('location', 'force'):
            d = {
                'screen_x': self.root['x'],
                'screen_y': self.root['y'],
                'screen_w': self.root['w'],
                'screen_h': self.root['h'],
                'win_w': win_width,
                'win_h': win_height
                }
            # loc_data is [gravity, x_expr, y_expr]
            loc_data = (self.t.value('location', 'x'),
                        self.t.value('location', 'y'))

            location = (eval(loc_data[0], d), eval(loc_data[1], d))
            self.set_gravity(self.t.value('location', 'gravity'))

        screen = self.get_screen()

        self.move(location[0], location[1])

        new_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                         win_width, win_height)
        text_spacing = self.t.value('dimensions', 'text-spacing')
        text_offset = padding + text_spacing
        text_width = (width - 2 * text_spacing)
        if self.image != None:
            text_offset += self.t.value('image', 'size') + text_spacing
            text_width -= text_spacing
            text_width -= self.t.value('image', 'size')

        try:
            # base transparent window
            cr = pangocairo.CairoContext(cairo.Context(new_surface))
            cr.set_operator(cairo.OPERATOR_SOURCE)
            cr.set_source_rgba(0, 0, 0, 0)
            cr.paint()

            bk = 'urgency-{0}'.format(self.n.urgency)
            while 'same-as' in self.t.value(bk):
                bk = self.t.value(bk, 'same-as')

            shad_w = self.t.value('shadow', 'width')
            # urgency-based drop shadow
            cr.set_source_rgba(*self.t.value(bk, 'shadow-color'))
            cnote.util.cairo_rounded_rect(cr, 1.0,
                                          padding - shad_w,
                                          padding - shad_w,
                                          self.t.value('dimensions',
                                                       'corner-radius'),
                                          width + 2 * shad_w,
                                          height + 2 * shad_w)

            cr.fill()
            cnote.cairo_blur.gaussian_blur(new_surface,
                                           self.t.value('shadow', 'blur'))

            # background
            cr.set_source_rgba(*self.t.value(bk, 'background-color'))
            cnote.util.cairo_rounded_rect(cr, 1.0, padding, padding,
                                          self.t.value('dimensions',
                                                       'corner-radius'),
                                          width, height)
            cr.fill()

            # summary
            cr.set_line_width(1.0)
            cr.set_operator(cairo.OPERATOR_SOURCE)
            cr.set_source_rgba(*self.t.value(bk, 'title-text', 'color'))
            cr.new_path()
            cr.move_to(text_offset, padding + text_spacing)

            layout = cr.create_layout()
            layout.set_text(self.n.summary)
            layout.set_width(pango.SCALE * text_width)
            layout.set_font_description(self.get_font(self.t.value(
                        bk, 'title-text', 'font')))
            pangocairo.context_set_font_options(layout.get_context(),
                                                screen.get_font_options())
            cr.update_layout(layout)
            cr.show_layout(layout)

            # body
            cr.set_source_rgba(*self.t.value(bk, 'body-text', 'color'))
            cr.new_path()
            cr.move_to(text_offset,
                       padding + layout.get_pixel_size()[1] +
                       int(text_spacing * 1.5))

            if self.t.value('miscellaneous', 'strip-markup'):
                layout.set_text(cnote.util.strip_markup(self.n.body))
            else:
                layout.set_markup(self.n.body)

            layout.set_width(pango.SCALE * text_width)
            layout.set_font_description(self.get_font(self.t.value(bk,
                                                                   'body-text',
                                                                   'font')))
            pangocairo.context_set_font_options(layout.get_context(),
                                                screen.get_font_options())
            cr.update_layout(layout)
            cr.show_layout(layout)

            # image, if available
            if self.image != None:
                cr.set_operator(cairo.OPERATOR_OVER)
                gdkcr = gtk.gdk.CairoContext(cr)
                gdkcr.set_source_pixbuf(self.image,
                                        padding + text_spacing,
                                        padding + text_spacing)
                gdkcr.paint_with_alpha(self.t.value('image', 'opacity'))

            self.surface = new_surface
        except Exception as ex:
            logging.error(ex)

    def resize_window_as_needed(self, padding):
        max_width = self.t.value('dimensions', 'width', 'maximum')
        min_width = self.t.value('dimensions', 'width', 'minimum')
        min_height = self.t.value('dimensions', 'height', 'minimum')
        text_spacing = self.t.value('dimensions', 'text-spacing')
        text_width = max_width - 2 * text_spacing

        bk = 'urgency-{0}'.format(self.n.urgency)
        while 'same-as' in self.t.value(bk):
            bk = self.t.value(bk, 'same-as')

        if self.image != None:
            text_width -= text_spacing
            text_width -= self.t.value('image', 'size')

        layout = pango.Layout(self.create_pango_context())
        layout.set_font_description(self.get_font(self.t.value(bk,
                                                               'title-text',
                                                               'font')))
        layout.set_text(self.n.summary)
        layout.set_width(text_width * pango.SCALE)
        t_width, t_height = layout.get_pixel_size()

        layout.set_font_description(self.get_font(self.t.value(bk,
                                                               'body-text',
                                                               'font')))
        if self.t.value('miscellaneous', 'strip-markup'):
            layout.set_text(cnote.util.strip_markup(self.n.body))
        else:
            layout.set_markup(self.n.body)
        layout.set_width(text_width * pango.SCALE)
        b_width, b_height = layout.get_pixel_size()

        width = 2 * text_spacing + (b_width if
                                    b_width > t_width else t_width)
        height = int(2.5 * text_spacing) + b_height + t_height

        if self.image != None:
            width += text_spacing + self.t.value('image', 'size')

        if width < min_width:
            width = min_width

        if height < min_height:
            height = min_height

        logging.debug("size should be '{0}x{1}'".format(width, height))
        self.resize(width + padding * 2, height + padding * 2)
        return (width, height)

    def get_font(self, hint):
        fd = pango.FontDescription()
        if 'family' in hint:
            fd.set_family(hint['family'])
        if 'style' in hint:
            fd.set_style(hint['style'])
        if 'variant' in hint:
            fd.set_variant(hint['variant'])
        if 'weight' in hint:
            fd.set_weight(hint['weight'])
        if 'stretch' in hint:
            fd.set_stretch(hint['stretch'])
        if 'size' in hint:
            fd.set_size(int(hint['size'] * pango.SCALE))
        return fd

    def try_load_image(self):
        self.image = None

        # (hint-name, load-function, is-deprecated) in order of preference
        items = [
            ('image-data', cnote.util.load_pixbuf_fromdata, False),
            ('image_data', cnote.util.load_pixbuf_fromdata, True),
            ('image-path', cnote.util.load_pixbuf_fromname, False),
            ('image_path', cnote.util.load_pixbuf_fromname, True),
            ('icon_data', cnote.util.load_pixbuf_fromdata, True)
            ]

        for h in items:
            if h[0] in self.n.hints:
                logging.debug('using {0} for notification image'.format(h[0]))
                if h[2]:
                    logging.warn("'{0}' using deprecated hint '{1}'".format(
                            self.n.name, h[0]))
                self.image = h[1](self.n.hints[h[0]], self.t.value('image',
                                                                   'size'))
                if self.image != None:
                    return

        # if no hint was provided, fall back on the icon name
        if len(self.n.icon) != 0:
            logging.debug('using icon for notification image')
            self.image = cnote.util.load_pixbuf_fromname(self.n.icon,
                                                         self.t.value('image',
                                                                      'size'))
