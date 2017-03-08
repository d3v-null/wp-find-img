# -*- coding: utf-8 -*-
import tldextract
from urlparse import urlparse, urlunparse
from urlparse import urlsplit, urlunsplit
from urlparse import ParseResult

class URLHelpers(object):
    test=0

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
