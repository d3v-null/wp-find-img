# -*- coding: utf-8 -*-

import scrapy
from scrapy.crawler import CrawlerProcess
from argparse import ArgumentParser

from spiders.img_spider import ImgSpider

def main():
    argParser = ArgumentParser(
        description="find redundant images in a wordpress site"
    )

    argParser.add_argument('--start-urls',
        help="comma separated list of urls to start scraping",
        required=True
    )

    args = argParser.parse_args()
    spider_args = {}
    crawler_settings = {
        'ITEM_PIPELINES':{
            'wp_find_img.pipelines.DuplicatesPipeline': 100,
            'wp_find_img.pipelines.JsonWriterPipeline': 200
        }
    }
    if args:
        spider_args['start_urls'] = args.start_urls.split(',')

    process = CrawlerProcess(crawler_settings)
    process.crawl(ImgSpider, **spider_args)
    process.start()

if __name__ == '__main__':
    main()
