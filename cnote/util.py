import re
import htmlentitydefs
import math
import gtk
import logging

def strip_markup(text):
    text = re.sub('<[^<]+?>', '', text)
    # the below doesn't seem to handle '&apos;'
    text = re.sub('&apos;', "'", text)

    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is
    return re.sub("&#?\w+;", fixup, text)


def cairo_rounded_rect(cr, aspect, x, y, corner_radius, width, height):
    radius = float(corner_radius) / aspect

    cr.move_to(x + radius, y)

    cr.line_to(x + width - radius, y)

    cr.arc(x + width - radius,
           y + radius,
           radius,
           -90.0 * math.pi / 180.0,
           0.0 * math.pi / 180.0)

    cr.line_to(x + width, y + height - radius)

    cr.arc(x + width - radius,
           y + height - radius,
           radius,
           0.0 * math.pi / 180.0,
           90.0 * math.pi / 180.0)

    cr.line_to(x + radius, y + height)

    cr.arc(x + radius,
           y + height - radius,
           radius,
           90.0 * math.pi / 180.0,
           180.0 * math.pi / 180.0)

    cr.line_to(x, y + radius)

    cr.arc(x + radius,
           y + radius,
           radius,
           180.0 * math.pi / 180.0,
           270.0 * math.pi / 180.0)


def load_pixbuf_fromname(filename, size):
    if filename.startswith('file://'):
        filename = filename[7:]

    if filename.startswith('/'):
        return gtk.gdk.pixbuf_new_from_file_at_scale(filename,
                                                     size,
                                                     size,
                                                     True)
    else:
        theme = gtk.icon_theme_get_default()
        return theme.load_icon(filename,
                               size,
                               gtk.ICON_LOOKUP_FORCE_SVG |
                               gtk.ICON_LOOKUP_GENERIC_FALLBACK |
                               gtk.ICON_LOOKUP_FORCE_SIZE)


def load_pixbuf_fromdata(data, size):
    width  = int(data[0])
    height = int(data[1])
    rowstride = int(data[2])
    has_alpha = bool(data[3])
    bits_per_sample = int(data[4])
    num_channels = int(data[5])
    pixels = ''.join([chr(i) for i in data[6]])

    # some images complain about being a few bytes too short;
    # not sure what the issue is, but the below resolves it for now
    # in spectacularly hackish fashion
    pixels += "\0\0\0\0"

    try:
        logging.debug('w={0},h={1},r={2},a={3},bps={4},c={5}'.format(
                width, height, rowstride, has_alpha, bits_per_sample,
                num_channels))
        image = gtk.gdk.pixbuf_new_from_data(pixels,
                                             gtk.gdk.COLORSPACE_RGB,
                                             has_alpha,
                                             bits_per_sample,
                                             width,
                                             height,
                                             rowstride)
        return scale_pixbuf(image, size)
    except ValueError as err:
        logging.error('failed to load image from data: {0}'.format(err))
        return None


def scale_pixbuf(pixbuf, size):
    w = pixbuf.get_width()
    h = pixbuf.get_height()

    max_edge = w if w > h else h

    new_w = int(size * (float(w) / float(max_edge)))
    new_h = int(size * (float(h) / float(max_edge)))

    scaled_img = pixbuf.scale_simple(new_w, new_h,
                                     gtk.gdk.INTERP_BILINEAR)

    # a perfect square!
    if w == h:
        return scaled_img

    # otherwise we need to center it
    new_img = gtk.gdk.Pixbuf(scaled_img.get_colorspace(),
                             True,
                             scaled_img.get_bits_per_sample(),
                             size,
                             size)
    new_img.fill(0)
    dest_x = dest_y = 0

    if new_w > new_h:
        dest_y = int((new_w - new_h) / 2)
    else:
        dest_x = int((new_h - new_w) / 2)

    scaled_img.copy_area(0, 0,
                         scaled_img.get_width(),
                         scaled_img.get_height(),
                         new_img,
                         dest_x, dest_y)
    return new_img
