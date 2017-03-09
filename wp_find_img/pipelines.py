# -*- coding: utf-8 -*-

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

from scrapy.utils.misc import md5sum
from scrapy.exceptions import DropItem
from scrapy.settings import Settings
from scrapy.pipelines.images import ImagesPipeline
from scrapy.pipelines.images import NoimagesDrop, ImageException

import helpers

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

        self.dhash_store = {}

    def image_downloaded(self, response, request, info):
        checksum = None
        for path, image, buf in self.get_image(response, request, info):
            if checksum is None:
                buf.seek(0)
                checksum = md5sum(buf)
            width, height = image.size
            self.store.persist_file(
                path, buf, info,
                meta={'width': width, 'height': height},
                headers={'Content-Type': 'image/jpeg'})
            dhash = helpers.dhash(image, hash_size = 16)
            self.dhash_store[checksum] = dhash
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
        yield path, image, buf

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
            if 'checksum' in image_info:
                checksum = image_info.get('checksum', None)
                if checksum in self.dhash_store:
                    image_info['dhash'] = self.dhash_store[checksum]
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
