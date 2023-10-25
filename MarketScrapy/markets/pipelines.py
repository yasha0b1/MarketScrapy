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
        def prepare_common_attributes(Market_ID, Market_Name,Contract_ID,Contract_Name):
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
        def prepare_measure(measure_name, measure_value, measure_type):
            measure = {
                'Name': measure_name,
                'Value': str(measure_value),
                'Type': measure_type
            }
            return measure
        time = datetime.utcnow().isoformat()
        for contract in item['Contracts']:
            contractsItemDict=defaultdict(def_value)
            for field in MarketContractsItem.fields.keys():
                contractsItemDict[field] = contract.get(field)
            for field in ContractContractsItem.fields.keys():
                contractsItemDict[field] = contract.get(field)
            current_time = self._current_milli_time()



            common_attributes = prepare_common_attributes(str(item['ID']),
                                                          str(item['Name']),
                                                          str(contractsItemDict['ID'] if contractsItemDict['ID'] else contractsItemDict['ContractId']),
                                                          str(contractsItemDict['Name'] if contractsItemDict['Name'] else contractsItemDict['ContractName'])    )
            record = prepare_record(current_time)




            contractBestNoPrice=contractsItemDict['BestNoPrice'] if contractsItemDict['BestNoPrice'] else contractsItemDict['BestBuyNoCost']
            if contractBestNoPrice is not None:
                record['MeasureValues'].append(prepare_measure('BestNoPrice', contractBestNoPrice,'DOUBLE'))
            contractBestBuyYesCost=contractsItemDict['BestYesPrice'] if contractsItemDict['BestYesPrice'] else contractsItemDict['BestBuyYesCost']
            if contractBestBuyYesCost is not None:
                record['MeasureValues'].append(prepare_measure('BestYesPrice', contractBestBuyYesCost,'DOUBLE'))
            contractLastClosePrice=contractsItemDict['LastClosePrice']
            if contractLastClosePrice is not None:
                record['MeasureValues'].append(prepare_measure('LastClosePrice', contractLastClosePrice,'DOUBLE'))
            contractLastTradePrice=contractsItemDict['LastTradePrice']
            if contractLastTradePrice is not None:
                record['MeasureValues'].append(prepare_measure('LastTradePrice', contractLastTradePrice,'DOUBLE'))
            contractBestYesQuantity=contractsItemDict['BestYesQuantity']
            if contractBestYesQuantity is not None:
                record['MeasureValues'].append(prepare_measure('BestYesQuantity', contractBestYesQuantity,'BIGINT'))
            contractBestNoQuantity=contractsItemDict['BestNoQuantity']
            if contractBestNoQuantity is not None:
                record['MeasureValues'].append(prepare_measure('BestNoQuantity', contractBestNoQuantity,'BIGINT'))
            records=[record]
            try:
                _logging.info(f'records:{records}')
                result = self.client.write_records(DatabaseName=settings.DATABASE_NAME,
                                                   TableName=settings.TABLE_NAME,
                                                   Records=records,
                                                   CommonAttributes=common_attributes)
                _logging.info(f'result:{result}')
            except self.client.exceptions.RejectedRecordsException as err:
                _logging.info(f'Error:{err}')
            except Exception as err:
                _logging.info(f'Error:{err}')
            _logging.info(f'item.contract:{contract}')
        return item
    def close_spider(self, spider):
        logging.info('close Timestream...')
