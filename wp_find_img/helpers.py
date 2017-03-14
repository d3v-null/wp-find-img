# -*- coding: utf-8 -*-
import time

from urlparse import urlparse, urlunparse
from urlparse import urlsplit, urlunsplit
from urlparse import ParseResult

from PIL import Image
import tldextract

class URLHelpers(object):
    """ A set of helpers for URL stuff """

    @classmethod
    def only_domain(cls, url):
        """Extracts only the domain part of the url, excluding the subdomain """
        try:
            ext = tldextract.extract(url)
        except TypeError as e:
            raise UserWarning("could not extract url {url} because of exception {e} ".format(
                url=url,
                e=e
            ))
        return '.'.join(
            part for part in [
                ext.domain,
                ext.suffix
            ] if part
        )

    @classmethod
    def no_dynamic(cls, url):
        """Removes the fragment, params and query part of the url"""
        parsed = urlsplit(url)
        return urlunsplit(
            parsed[:3] + ('', '')
        )

    @classmethod
    def within_domain(cls, url, domain):
        url_domain = cls.only_domain(url)
        return url_domain == domain

#

class TimeHelpers:
    """ A set of helpers for time stuff """

    safeTimeFormat = "%Y-%m-%d_%H-%M-%S"

    @classmethod
    def starStrptime(cls, string, fmt=None ):
        if fmt==None:
            fmt=cls.safeTimeFormat
        string = unicode(string)
        response = 0
        if(string):
            tstruct = time.strptime(string, fmt)
            if(tstruct):
                response = time.mktime(tstruct)
        return response

    @classmethod
    def safeStrpTime(cls, string):
        return cls.starStrptime(string, cls.safeTimeFormat)

    @classmethod
    def safeTimeToString(cls, t, fmt=None):
        if fmt==None:
            fmt = cls.safeTimeFormat
        return time.strftime(fmt, time.localtime(t))

    @classmethod
    def hasHappenedYet(cls, t):
        assert isinstance(t, (int, float)), "param must be an int not %s"% type(t)
        return t >= time.time()

    @classmethod
    def getSafeTimeStamp(cls):
        return time.strftime(cls.safeTimeFormat)

# borrowed from here: http://blog.iconfinder.com/detecting-duplicate-images-using-python/

def dhash(image, hash_size = 8):
    # Grayscale and shrink the image in one step.
    image = image.convert('L').resize(
        (hash_size + 1, hash_size),
        Image.ANTIALIAS,
    )

    # Compare adjacent pixels.
    difference = []
    for row in xrange(hash_size):
        for col in xrange(hash_size):
            pixel_left = image.getpixel((col, row))
            pixel_right = image.getpixel((col + 1, row))
            difference.append(pixel_left > pixel_right)

    # Convert the binary array to a hexadecimal string.
    decimal_value = 0
    hex_string = []
    for index, value in enumerate(difference):
        if value:
            decimal_value += 2**(index % 8)
        if (index % 8) == 7:
            hex_string.append(hex(decimal_value)[2:].rjust(2, '0'))
            decimal_value = 0

    return ''.join(hex_string)
