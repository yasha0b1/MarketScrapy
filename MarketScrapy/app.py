
import json

# useful for handling different item types with a single interface
from scrapy.utils.project import get_project_settings

import logging
import traceback
from datetime import datetime
import scrapy
import urllib.parse
from scrapy.crawler import CrawlerProcess
import scrapy.crawler as crawler
from scrapy.utils.log import configure_logging
from scrapy.loader import ItemLoader
from markets.items import MarketsItem, ContractContractsItem, MarketContractsItem
from markets.settings import MARKET_WATCHLIST
from multiprocessing import Process, Pipe
from twisted.internet import reactor

_logging = logging.getLogger('__name__')

_logging.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

_logging.addHandler(handler)


def build_url(base_url, path, args_dict):
    # Returns a list in the structure of urlparse.ParseResult
    url_parts = list(urllib.parse.urlparse(base_url))
    url_parts[2] = path
    url_parts[4] = urllib.parse.urlencode(args_dict)
    return urllib.parse.urlunparse(url_parts)

class MarketSpider(scrapy.Spider):
    name = "markets"
    def start_requests(self):
        query = {}
        base_url='https://www.predictit.org/'
        path='api/marketdata/all'
        urls = [
            build_url(base_url,path,query),
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)
    def parse(self, response):
        time = datetime.utcnow().isoformat()
        base_url = 'https://www.predictit.org/'
        base_path = 'api/Market/'
        query = {}
        for market in response.css('MarketData'):
            loader = ItemLoader(item=MarketsItem(), selector=market)
            loader.add_css('ID', 'ID::text')
            loader.add_css('Name', 'Name::text')
            loader.add_css('URL', 'URL::text')
            loader.add_value('Time', time)
            maket_id =  market.css('ID::text').get()
            self.log(f'market_id:{maket_id}')
            if maket_id in MARKET_WATCHLIST:
                path = base_path + maket_id + '/Contracts'
                url = build_url(base_url, path, query)
                self.log(f'url: {url}')
                yield  scrapy.Request(url=url, callback=self.parse_contracts,meta={'loader':loader})
            else:
                self.log(f'parse: MarketContracts')
                item = MarketContractsItem
                loader.add_value('Contracts', self.get_contracts(market,item))
                yield loader.load_item()
    def parse_contracts(self, response):
        loader=response.meta["loader"]
        item=ContractContractsItem
        loader.add_value('Contracts', self.get_contracts(response,item))
        yield loader.load_item()
    def get_contracts(self, contracts, item):
        contract_attr = [field for field in item.fields.keys()]
        for contract in contracts.css('ContractListResourceModel'):
            loader = ItemLoader(item=item(), selector=contract)
            for attr in contract_attr:
                loader.add_css(attr, attr + '::text')
            temp=loader.load_item()
            self.log(f'ContractListResourceModel.temp: {temp}')
            yield  temp
        for contract in contracts.css('MarketContract'):
            loader = ItemLoader(item=item(), selector=contract)
            for attr in contract_attr:
                loader.add_css(attr, attr + '::text')
            temp=loader.load_item()
            self.log(f'MarketContract.temp: {temp}')
            yield  temp
        # filename = f'markets.xml'
        # with open(filename, 'wb') as f:
        #     f.write(response.body)
        # self.log(f'Saved file {filename}')

def run_spider(spider):
    def f(conn):
        try:
            runner = crawler.CrawlerRunner(get_project_settings())
            deferred = runner.crawl(spider)
            deferred.addBoth(lambda _: reactor.stop())
            reactor.run()
            conn.send(None)
        except Exception as e:
            conn.send(e)
        conn.close()
    parent_connections = []
    parent_conn, child_conn = Pipe()
    parent_connections.append(parent_conn)
    #q = Queue()
    p = Process(target=f, args=(child_conn,))
    p.start()
    p.join()



def lambda_handler(event, context):
    #process = CrawlerProcess(get_project_settings())
    #process.crawl(MarketSpider)
    #process.start(install_signal_handlers=False) # the script will block here until the crawling is finished
    configure_logging()
    run_spider(MarketSpider)




