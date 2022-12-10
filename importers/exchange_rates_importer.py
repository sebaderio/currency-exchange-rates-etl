from typing import List

import data_providers
import entities
import exceptions
import storage_providers
import value_objects


class ExchangeRatesImporter:
    def __init__(
        self,
        source: value_objects.Source,
        storage_type: value_objects.StorageType,
        base_currency: str,
    ) -> None:
        self._source = source
        self._base_currency = base_currency
        # strategy pattern
        self._init_storage_provider(storage_type)
        self._init_data_provider()

    def _init_storage_provider(self, storage_type: value_objects.StorageType) -> None:
        if storage_type == value_objects.StorageType.GCP_BIG_QUERY:
            self._storage = storage_providers.GcpBigQueryProvider()
        elif storage_type == value_objects.StorageType.POSTGRES:
            self._storage = storage_providers.PostgresProvider()
        elif storage_type == value_objects.StorageType.SQLITE:
            self._storage = storage_providers.SqliteProvider()
        else:
            raise NotImplementedError

    def _init_data_provider(self) -> None:
        if self._source == value_objects.Source.ECB:
            self._data_provider = data_providers.EcbDataProvider()
        elif self._source == value_objects.Source.FC_API:
            self._data_provider = data_providers.FreeCurrencyDataProvider()
        else:
            raise NotImplementedError

    def run_import(self) -> None:
        try:
            new_exchange_rates = self._data_provider.get_exchange_rates(self._base_currency)
        except exceptions.FailedToFetchExchangeRatesFromExternalSource as exc:
            print(
                f"{exc}\nThere are no new exchange rates for source {self._source.value}. "
                "Trying to fill missing records with the latest available values from the past..."
            )
            new_exchange_rates = []
        latest_exchange_rates_in_db = self._storage.get_latest_exchange_rates(self._source, self._base_currency)
        exchange_rates_to_save = self._prepare_exchange_rates_to_save(new_exchange_rates, latest_exchange_rates_in_db)
        self._storage.insert_exchange_rates(exchange_rates_to_save)

    def _prepare_exchange_rates_to_save(
        self,
        new_exchange_rates: List[entities.ExchangeRate],
        latest_exchange_rates_in_db: List[entities.ExchangeRate],
    ) -> List[entities.ExchangeRate]:
        # TODO implement logic that checks the current status of data in data warehouse
        # and prepares data to be saved accordingly.
        for exchange_rate in new_exchange_rates:
            exchange_rate.date = '2022-12-05'
        return new_exchange_rates
