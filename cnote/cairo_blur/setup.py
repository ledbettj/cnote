#!/usr/bin/env python

from distutils.core import setup, Extension

mod = Extension('cairo_blur',
                include_dirs = ['/usr/include/cairo',
                                '/usr/include/glib-2.0',
                                '/usr/lib/glib-2.0/include',
                                '/usr/include/pixman-1',
                                '/usr/include/freetype2',
                                '/usr/include/libpng12'],
                libraries = ['cairo', 'pthread'],
                sources = ['cairo_blur.c'])

setup(name='cairo_blur',
      version='0.1',
      ext_modules=[mod])

