# -*- coding: utf-8 -*-

import logging
import json

from scrapy.exceptions import DropItem

class DuplicatesPipeline(object):

    def __init__(self):
        self.ids_seen = set()
        self.logger = logging.getLogger('DuplicatesPipeline')

    def process_item(self, item, spider):
        if item['src'] in self.ids_seen:
            spider.logger.debug("not new: {item}".format(item=item))
            raise DropItem("Duplicate item found: %s" % item)
        else:
            spider.logger.debug("new: {item}".format(item=item))
            self.ids_seen.add(item['src'])
            return item

class JsonWriterPipeline(object):

    def __init__(self, *args, **kwargs):
        super(JsonWriterPipeline, self).__init__(*args, **kwargs)
        self.file=None

    def open_spider(self, spider):
        self.file = open('items.jl', 'wb')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(dict(item)) + "\n"
        self.file.write(line)
        return item
