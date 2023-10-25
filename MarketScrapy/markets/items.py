
# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from scrapy.item import Item, Field
from scrapy.loader.processors import MapCompose, TakeFirst
import scrapy

def process_float_or_int(value):
    try:
        return eval(value)
    except:
        return value

class MarketsItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    ID = Field(output_processor=TakeFirst())
    Name = Field(output_processor=TakeFirst())
    URL = Field(output_processor=TakeFirst())
    Time = Field(output_processor=TakeFirst())
    Contracts = Field()

offerCountNew = scrapy.Field(input_processor = MapCompose(lambda x: process_float_or_int(x)), output_processor = TakeFirst())

class MarketContractsItem(scrapy.Item):
    Name = Field(output_processor=TakeFirst())
    ID = Field(output_processor=TakeFirst())
    LastTradePrice = Field(input_processor = MapCompose(lambda x: process_float_or_int(x)), output_processor = TakeFirst())
    BestBuyNoCost = Field(input_processor = MapCompose(lambda x: process_float_or_int(x)), output_processor = TakeFirst())
    BestBuyYesCost = Field(input_processor = MapCompose(lambda x: process_float_or_int(x)), output_processor = TakeFirst())
    LastClosePrice = Field(input_processor = MapCompose(lambda x: process_float_or_int(x)), output_processor = TakeFirst())



class ContractContractsItem(scrapy.Item):
    ContractName = Field(output_processor=TakeFirst())
    ContractId = Field(output_processor=TakeFirst())
    LastTradePrice = Field(input_processor = MapCompose(lambda x: process_float_or_int(x)), output_processor = TakeFirst())
    BestNoPrice = Field(input_processor = MapCompose(lambda x: process_float_or_int(x)), output_processor = TakeFirst())
    BestYesPrice = Field(input_processor = MapCompose(lambda x: process_float_or_int(x)), output_processor = TakeFirst())
    LastClosePrice = Field(input_processor = MapCompose(lambda x: process_float_or_int(x)), output_processor = TakeFirst())
    BestYesQuantity = Field(input_processor = MapCompose(lambda x: process_float_or_int(x)), output_processor = TakeFirst())
    BestNoQuantity = Field(input_processor = MapCompose(lambda x: process_float_or_int(x)), output_processor = TakeFirst())


