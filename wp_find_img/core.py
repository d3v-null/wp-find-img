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

    argParser.add_argument('--img-store',
        help="location on disk where images are stored",
        required=True
    )

    argParser.add_argument('--db-store',
        help="location on disk of hash database",
        required=True
    )

    spider_args = {}
    crawler_settings = {
        'IMAGES_URLS_FIELD':'image_urls',
        'IMAGES_RESULT_FIELD':'images',
        'IMAGES_THUMBS':{
            'smol': (9,8)
        },
        'ITEM_PIPELINES':{
            'wp_find_img.pipelines.ImageHashesPipeline': 100,
            'wp_find_img.pipelines.DisplayDHashTablePipeline': 200,
            'wp_find_img.pipelines.JsonWriterPipeline': 200,
        }
    }
    args = argParser.parse_args()
    if args:
        if args.start_urls:
            spider_args['start_urls'] = args.start_urls.split(',')
        if args.img_store:
            crawler_settings['IMAGES_STORE'] = args.img_store
        if args.db_store:
            crawler_settings['DB_STORE'] = args.db_store

    process = CrawlerProcess(crawler_settings)
    process.crawl(ImgSpider, **spider_args)
    process.start()

if __name__ == '__main__':
    main()
