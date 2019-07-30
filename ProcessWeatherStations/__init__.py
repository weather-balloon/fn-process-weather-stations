import logging
import json
import os
from io import StringIO
from typing import List, Dict

import azure.functions as func
from azure.cosmosdb.table import TableService, TableBatch, Entity
from parse_bom_stations import parse_station_list, WeatherStationTuple


def create_entity(station: WeatherStationTuple) -> dict:
    """ Conversion from input data to desired properties and types """

    entity = Entity()
    entity.provider = 'bom'
    entity.country = 'Australia'
    entity.country_code = 'AU'
    entity.state = station.state
    entity.site = station.site
    entity.name = station.name
    entity.start_year = station.start_year
    entity.end_year = station.end_year

    location = {
        'type': "point",
        'coordinates': [float(station.longitude), float(station.latitude)]
    }
    entity.location = json.dumps(location)

    entity.PartitionKey = f"{entity.country_code}.{entity.state}"
    entity.RowKey = entity.site

    return entity

# Refer to https://docs.microsoft.com/en-au/azure/azure-functions/functions-bindings-storage-table#output


class BatchManager:
    def __init__(self, table_service: TableService, table_name: str, max_batch_size=100):
        self.partition_dict: Dict[str, List[Entity]] = {}
        self.table_service = table_service
        self.table_name = table_name
        self.max_batch_size = max_batch_size

    def add_entity(self, entity: Entity):
        if entity.PartitionKey not in self.partition_dict:
            self.partition_dict[entity.PartitionKey] = []

        self.partition_dict[entity.PartitionKey].append(entity)

    def _process_batch(self, entity_list):
        for segment in [entity_list[i * self.max_batch_size:(i + 1) * self.max_batch_size] for i in range((len(entity_list) + self.max_batch_size - 1) // self.max_batch_size)]:
            batch = TableBatch()
            for entity in segment:
                batch.insert_or_replace_entity(entity)

            logging.info(f"Committing batch size {len(segment)}")
            self.table_service.commit_batch(self.table_name, batch)

    def process(self):
        for entity_list in self.partition_dict.values():
            self._process_batch(entity_list)


async def main(stationData: func.InputStream):
    logging.info(
        f"Python blob trigger function processed blob ({stationData.name}) - {stationData.length} bytes")

    table_service = TableService(
        connection_string=os.environ['ConnectionStrings:TableBindingConnection'])

    table_name = 'WeatherStations'
    table_service.create_table(table_name, fail_on_exist=False)

    batch_manager = BatchManager(table_service, table_name)

    bytes_data = stationData.read()

    station_data = StringIO(str(bytes_data, 'ascii'), newline="\n")

    station_list = parse_station_list(station_data)

    logging.info(f"Processing {len(station_list)} records")

    for record in station_list:
        entity = create_entity(record)
        batch_manager.add_entity(entity)

    batch_manager.process()

    logging.info(f"Updated {table_name} - {len(station_list)} records")
