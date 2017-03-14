# -*- coding: utf-8 -*-

import os
import functools
import hashlib
import logging
import json
import six
from collections import namedtuple

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

from PIL import Image
from tabulate import tabulate
from requests import Request

from scrapy.utils.misc import md5sum
from scrapy.utils.python import to_bytes
from scrapy.exceptions import DropItem
from scrapy.settings import Settings
from scrapy.pipelines.images import ImagesPipeline
from scrapy.pipelines.images import NoimagesDrop, ImageException
from scrapy.pipelines.media import MediaPipeline

import helpers
import db

class JsonWriterPipeline(object):

    def __init__(self, *args, **kwargs):
        super(JsonWriterPipeline, self).__init__(*args, **kwargs)
        self.file=None

    def open_spider(self, spider):
        if spider: pass # avoid pep8 warnings
        self.file = open('items.jl', 'wb')

    def close_spider(self, spider):
        if spider: pass # avoid pep8 warnings
        self.file.close()

    def process_item(self, item, spider):
        if spider: pass # avoid pep8 warnings
        line = json.dumps(dict(item)) + "\n"
        self.file.write(line)
        return item

class ImageHashesPipeline(ImagesPipeline):
    # DEFAULT_IMAGES_HASHES_FIELD = "images_hashes"
    # IMAGES_TARGET_MODE = "L"

    def __init__(self, *args, **kwargs):
        super(ImageHashesPipeline, self).__init__(*args, **kwargs)

        # settings = kwargs.get('settings', None)
        #
        # if isinstance(settings, dict) or settings is None:
        #     settings = Settings(settings)
        #
        # resolve = functools.partial(self._key_for_pipe,
        #     base_class_name="ImageHashesPipeline",
        #     settings=settings
        # )

        # if not hasattr(self, "IMAGES_HASHES_FIELD"):
        #     self.IMAGES_HASHES_FIELD = self.DEFAULT_IMAGES_HASHES_FIELD
        #
        # self.images_hashes_field = settings.get(
        #     resolve('IMAGES_HASHES_FIELD'),
        #     self.IMAGES_HASHES_FIELD
        # )

        # self.images_target_mode = settings.get(
        #     resolve('IMAGES_TARGET_MODE'),
        #     self.IMAGES_TARGET_MODE
        # )

        self.url_meta = {}

    def image_downloaded(self, response, request, info):
        path, image, buf = self.get_image(response, request, info)
        width, height = image.size
        self.store.persist_file(
            path, buf, info,
            meta={'width': width, 'height': height},
            headers={'Content-Type': 'image/jpeg'})
        buf.seek(0)
        checksum = md5sum(buf)
        buf.seek(0, os.SEEK_END)
        bufflen = buf.tell()
        dhash = helpers.dhash(image, hash_size = 16)
        url = request.url
        if not url in self.url_meta:
            self.url_meta[url] = {}
        self.url_meta[url]['dhash'] = dhash
        self.url_meta[url]['bufflen'] = bufflen
        self.url_meta[url]['dimensions'] = (width, height)
        return checksum

    def get_image(self, response, request, info):
        """ See: parent get_images, but only does a single image """
        path = self.file_path(request, response=response, info=info)
        orig_image = Image.open(BytesIO(response.body))

        width, height = orig_image.size
        if width < self.min_width or height < self.min_height:
            raise ImageException("Image too small (%dx%d < %dx%d)" %
                                 (width, height, self.min_width, self.min_height))

        image, buf = self.convert_image(orig_image)
        return path, image, buf

        # for thumb_id, size in six.iteritems(self.thumbs):
        #     thumb_path = self.thumb_path(request, thumb_id, response=response, info=info)
        #     thumb_image, thumb_buf = self.convert_image(image, size)
        #     yield thumb_path, thumb_image, thumb_buf

    # def convert_image_mode(self, image, size=None, target_mode=None):
    #     """ see: parent convert_image, but instead of only RGBA target mode,
    #         can set arbitrary mode of converted image """
    #
    #     if not target_mode:
    #         target_mode = self.images_target_mode
    #     if image.format == 'PNG' and image.mode == 'RGBA':
    #         background = Image.new('RGBA', image.size, (255, 255, 255))
    #         background.paste(image, image)
    #         image = background.convert(target_mode)
    #     elif image.mode != target_mode:
    #         image = image.convert(target_mode)
    #
    #     if size:
    #         image = image.copy()
    #         image.thumbnail(size, Image.ANTIALIAS)
    #
    #     buf = BytesIO()
    #     image.save(buf, 'JPEG')
    #     return image, buf

    def item_completed(self, results, item, info):
        image_paths = []
        if isinstance(item, dict) or self.images_result_field in item.fields:
            image_paths = [x for ok, x in results if ok]
        if not image_paths:
            raise DropItem("Item contains no images")
        for image_info in image_paths:
            if 'url' in image_info:
                url = image_info.get('url', None)
                if url in self.url_meta:
                    image_info['dhash'] = self.url_meta[url].get('dhash')
                    image_info['bufflen'] = self.url_meta[url].get('bufflen')
                    image_info['dimensions'] = self.url_meta[url].get('dimensions')
        item[self.images_result_field] = image_paths
        return item

class DisplayDHashTablePipeline(object):
    DHashTableEntry = namedtuple('DHashTableEntry', ['page', 'img', 'hash'])
    def __init__(self, *args, **kwargs):
        super(DisplayDHashTablePipeline, self).__init__(*args, **kwargs)
        self.hashes = None
        self.file = None

    def open_spider(self, spider):
        if spider: pass # avoid pep8 warnings
        self.file = open('hashes.txt', 'wb')
        self.hashes = []

    def close_spider(self, spider):
        table = None
        if self.hashes:
            table = tabulate(self.hashes)
        spider.logger.debug("table is: \n%s" % table)
        if table:
            self.file.write(table)
        self.file.close()

    def process_item(self, item, spider):
        if spider: pass # avoid pep8 warnings
        page_url = item['page_url']
        for image in item['images']:
            img_url = image.get('url')
            img_dhash = image.get('dhash')
            self.hashes.append(self.DHashTableEntry(page_url, img_url, img_dhash))
        return item

class StoreDHashPipeline(object):
    """ Stores new DHashes in the database """

    DB_STORE = 'hashes.sqlite'

    def __init__(self, *args, **kwargs):
        super(StoreDHashPipeline, self).__init__(*args, **kwargs)

        settings = kwargs.get('settings', None)

        if isinstance(settings, dict) or settings is None:
            settings = Settings(settings)

        resolve = functools.partial(self._key_for_pipe,
            base_class_name="ImageHashesPipeline",
            settings=settings
        )

        self.db_store = settings.get(
            resolve('DB_STORE'),
            self.DB_STORE
        )

        self.db = db.DBWrapper(self.db_store)

    def _key_for_pipe(self, key, base_class_name=None,
                      settings=None):
        """
        >>> MediaPipeline()._key_for_pipe("IMAGES")
        'IMAGES'
        >>> class MyPipe(MediaPipeline):
        ...     pass
        >>> MyPipe()._key_for_pipe("IMAGES", base_class_name="MediaPipeline")
        'MYPIPE_IMAGES'
        """
        class_name = self.__class__.__name__
        formatted_key = "{}_{}".format(class_name.upper(), key)
        if class_name == base_class_name or not base_class_name \
            or (settings and not settings.get(formatted_key)):
            return key
        return formatted_key

    def open_spider(self, spider):
        if spider: pass # avoid pep8 warnings

    def close_spider(self, spider):
        if spider: pass
        self.db.close()

    def process_item(self, item, spider):
        if spider: pass # avoid pep8 warnings
        page_url = item['page_url']
        scrape_time = spider.scrape_time
        for image_meta in item['images']:
            self.db.add_sighting(page_url, scrape_time, image_meta)

            # self.hashes.append(self.DHashTableEntry(page_url, img_url, img_dhash))
        return item
