




# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import logging
import boto3
import time
from itemadapter import ItemAdapter
from markets import settings
import traceback
from datetime import datetime
from markets.items import ContractContractsItem, MarketContractsItem
from collections import defaultdict
_logging = logging.getLogger('markets.pipelines')


class MarketsPipeline:

    # default constructor
    def __init__(self):
        self.write_api = None
        self.client = None
    def prepare_common_attributes(Market_Name,Market_ID,Contract_ID,Contract_Name):
        common_attributes = {
            'Dimensions': [
                {'Name': 'Market_Name', 'Value': Market_Name},
                {'Name': 'Market_ID', 'Value': Market_ID},
                {'Name': 'Contract_ID', 'Value': Contract_ID},
                {'Name': 'Contract_Name', 'Value': Contract_Name}
            ],
            'MeasureName': 'market_tick',
            'MeasureValueType': 'MULTI'
        }
        return common_attributes

    def prepare_record(current_time):
        record = {
            'Time': str(current_time),
            'MeasureValues': []
        }
        return record
    def prepare_measure(measure_name, measure_value):
        measure = {
            'Name': measure_name,
            'Value': str(measure_value),
            'Type': 'DOUBLE'
        }
        return measure



    def open_spider(self, spider):
        _logging.info('create influxdb connections...')
        try:
            self.client = boto3.client('timestream-write')
        except Exception as e:
            _logging.error('connection error: %s', traceback.format_exc())
    @staticmethod
    def _current_milli_time():
        return str(int(round(time.time() * 1000)))
    def process_item(self, item, spider):
        _logging.info("Item: "+str(item))
        measurements = []
        def def_value():
            return None
        time = datetime.utcnow().isoformat()
        for contract in item['Contracts']:
            contractsItemDict=defaultdict(def_value)
            for field in MarketContractsItem.fields.keys():
                contractsItemDict[field] = contract.get(field)
            for field in ContractContractsItem.fields.keys():
                contractsItemDict[field] = contract.get(field)


            current_time = self._current_milli_time()
            dimensions = [
                {'Name': 'Market_Name', 'Value': str(item['Name'])},
                {'Name': 'Market_ID', 'Value': str(item['ID'])},
                {'Name': 'Contract_ID', 'Value': str(contractsItemDict['ID'] if contractsItemDict['ID'] else contractsItemDict['ContractId'])},
                {'Name': 'Contract_Name', 'Value': str(contractsItemDict['Name'] if contractsItemDict['Name'] else contractsItemDict['ContractName'])}
            ]
            records=[]

            common_attributes = {
              'Dimensions': dimensions,
              'MeasureValueType': 'DOUBLE',
              'Time': current_time
            }
            contractBestNoPrice=contractsItemDict['BestNoPrice'] if contractsItemDict['BestNoPrice'] else contractsItemDict['BestBuyNoCost']
            if contractBestNoPrice is not None:
                BestNoPrice = {
                  'MeasureName': 'BestNoPrice',
                  'MeasureValue': str(contractBestNoPrice)
                }
                records.append(BestNoPrice)
            contractBestBuyYesCost=contractsItemDict['BestYesPrice'] if contractsItemDict['BestYesPrice'] else contractsItemDict['BestBuyYesCost']
            if contractBestBuyYesCost is not None:
                BestYesPrice = {
                  'MeasureName': 'BestYesPrice',
                  'MeasureValue': str(contractBestBuyYesCost)
                }
                records.append(BestYesPrice)
            contractLastClosePrice=contractsItemDict['LastClosePrice']
            if contractLastClosePrice is not None:
                LastClosePrice = {
                  'MeasureName': 'LastClosePrice',
                  'MeasureValue': str(contractLastClosePrice)
                }
                records.append(LastClosePrice)
            contractLastTradePrice=contractsItemDict['LastTradePrice']
            if contractLastTradePrice is not None:
                LastTradePrice = {
                  'MeasureName': 'LastTradePrice',
                  'MeasureValue': str(contractLastTradePrice)
                }
                records.append(LastTradePrice)
            contractBestYesQuantity=contractsItemDict['BestYesQuantity']
            if contractBestYesQuantity is not None:
                BestYesQuantity = {
                  'MeasureName': 'BestYesQuantity',
                  'MeasureValue': str(contractBestYesQuantity)
                }
                records.append(BestYesQuantity)
            contractBestNoQuantity=contractsItemDict['BestNoQuantity']
            if contractBestNoQuantity is not None:
                BestNoQuantity = {
                  'MeasureName': 'BestNoQuantity',
                  'MeasureValue': str(contractBestNoQuantity)
                }
                records.append(BestNoQuantity)

            try:
                _logging.info(f'records:{records}')
                _logging.info(f'dimensions:{dimensions}')
                result = self.client.write_records(DatabaseName=settings.DATABASE_NAME,
                                                   TableName=settings.TABLE_NAME,
                                                   Records=records,
                                                   CommonAttributes=common_attributes)
                _logging.info(f'result:{result}')
            except self.client.exceptions.RejectedRecordsException as err:
                _logging.info(f'Error:{err}')
            except Exception as err:
                _logging.info(f'Error:{err}')



            # measurement = Point(settings.INFLUX_DB_TABLE).tag('Market_URL',item['URL']) \
                    # .tag('Market_Name', item['Name']) \
                    # .tag('Market_ID', item['ID']) \
                    # .tag('Contract_ID', contractsItemDict['ID'] if contractsItemDict['ID'] else contractsItemDict['ContractId']) \
                    # .tag('Contract_Name', contractsItemDict['Name'] if contractsItemDict['Name'] else contractsItemDict['ContractName']) \
                    # .field('BestBuyNoCost', contractsItemDict['BestNoPrice'] if contractsItemDict['BestNoPrice'] else contractsItemDict['BestBuyNoCost']) \
                    # .field('BestBuyYesCost', contractsItemDict['BestYesPrice'] if contractsItemDict['BestYesPrice'] else contractsItemDict['BestBuyYesCost']) \
                    # .field('LastClosePrice', contractsItemDict['LastClosePrice']) \
                    # .field('LastTradePrice', contractsItemDict['LastTradePrice']) \
                    # .field('BestYesQuantity', contractsItemDict['BestYesQuantity']) \
                    # .field('BestNoQuantity', contractsItemDict['BestNoQuantity'])
            _logging.info(f'item.contract:{contract}')
            #self.write_api.write(bucket=settings.INFLUX_DB_BUCKET, record=p)
            #self.write_api.write(bucket=settings.INFLUX_DB_BUCKET, record=measurement)
        return item
    def close_spider(self, spider):
        logging.info('close influxdb connections...')





