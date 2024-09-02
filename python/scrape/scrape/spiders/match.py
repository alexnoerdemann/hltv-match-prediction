import scrapy


class MatchSpider(scrapy.Spider):
    # TODO[HMP-TASK-4]: Add docstring
    name = "match"
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        if "start_urls" in kwargs:
            spider.start_urls = kwargs.pop('start_urls').split(',')
        spider.allowed_domains = crawler.settings.get('SPIDER_ALLOWED_DOMAINS', [])

        return spider

    def parse(self, response):
        self.log("Parse Match Called.")
        self.log(self.start_urls)
