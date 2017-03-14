# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider
from scrapy.spiders import Rule

from context import wp_find_img
from wp_find_img.helpers import URLHelpers, TimeHelpers

# class ImgItem(scrapy.Item):
#     src = scrapy.Field()
#
# class LinkItem(scrapy.Item):
#     url = scrapy.Field()
#     text = scrapy.Field()
#     fragment = scrapy.Field()
#     nofollow = scrapy.Field()

class ImgPageItem(scrapy.Item):
    image_urls = scrapy.Field()
    images = scrapy.Field()
    page_url = scrapy.Field()

IMG_EXTENSIONS = [
    'mng', 'pct', 'bmp', 'gif', 'jpg', 'jpeg', 'png', 'pst', 'psp', 'tif',
    'tiff', 'ai', 'drw', 'dxf', 'eps', 'ps', 'svg'
]

IGNORED_EXTENSIONS_NOT_IMG = [
    ext for ext in scrapy.linkextractors.IGNORED_EXTENSIONS \
    if ext not in IMG_EXTENSIONS
]

class ImgSpider(CrawlSpider):
    name = "images"
    allowed_domains = []

    def __init__(self, *args, **kwargs):
        super(ImgSpider, self).__init__(*args, **kwargs)

        if hasattr(self, 'start_url'):
            start_url = getattr(self, 'start_url')
            if start_url:
                self.start_urls.append(start_url)

        for url in self.start_urls:
            target_domain = URLHelpers.only_domain(url)
            self.log("target domain: {domain}".format(domain=target_domain))
            if target_domain and target_domain not in self.allowed_domains:
                self.allowed_domains.append(target_domain)

        self.aLinkExtractor = LinkExtractor(
            # allow_domains=self.allowed_domains,
            # deny=['/wp-json/'],
            process_value=URLHelpers.no_dynamic,
        )

        self.imgLinkExtractor = LinkExtractor(
            # allow_domains=self.allowed_domains,
            # allow=['/wp-content/'],
            tags=['img'],
            attrs=['src'],
            deny_extensions=IGNORED_EXTENSIONS_NOT_IMG
        )

        self.rules = (
            Rule(self.aLinkExtractor, callback='parse_page', follow=True),
            # Rule(self.imgLinkExtractor, callback='parse_page'),
        )

        self._compile_rules()

        self.scrape_time = TimeHelpers.getSafeTimeStamp()


    # def parse_link(self, response):
    #     self.log("processing link: {response}".format(response=response))
    #
    #     for link in self.aLinkExtractor.extract_links(response):
    #         # self.log("link found: {link}".format(link=link))
    #         linkItem = LinkItem(
    #             url=link.url,
    #             text=link.text,
    #             fragment=link.fragment,
    #             nofollow=link.nofollow
    #         )
    #         yield linkItem
    #         # yield scrapy.Request(link.url, )

    def parse_page(self, response):
        self.log("processing link: {response}".format(response=response))
        img_links = []
        for link in self.imgLinkExtractor.extract_links(response):
            self.log("extractor found image: {link}".format(link=link))
            if link.url:
                within_domains = map(
                    lambda domain: URLHelpers.within_domain(link.url, domain),
                    self.allowed_domains
                )
                if any(within_domains):
                    self.logger.debug("{url} is within allowed domains: {domains}".format(
                        url=link.url, domains=self.allowed_domains
                    )),

                    img_links.append(link.url)
                else:
                    self.logger.debug("{url} is not within allowed domains: {domains}".format(
                        url=link.url, domains=self.allowed_domains
                    ))

        if img_links:
            final_url = response.url
            yield ImgPageItem(page_url=final_url, image_urls=img_links)

    # def parse_img(self, url):
    #     item = ImgItem(
    #         src=url
    #     )
    #     yield item
        #
        # for image in response.xpath('//img/@src').extract():
        #     self.log("found image: {image}".format(image=image))
        #     yield ImgItem(src=image)


        # self.log("finished processing response")

        # recursively call parse on links not seen yet

        # find all images
