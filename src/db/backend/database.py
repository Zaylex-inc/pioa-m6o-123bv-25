"""Абстрактный интерфейс базы данных."""

import logging
from abc import ABC, abstractmethod
from typing import Any

from .errors import (
    InvalidStorageDataError,
    TableAlreadyExistsError,
    TableNotFoundError,
)
from .table import Table


logger = logging.getLogger(__name__)


class Database(ABC):
    """Общий интерфейс БД. Конкретные реализации задают способ хранения."""

    def create_table(self, table_name: str, columns: tuple[str, ...]) -> None:
        if self._table_exists(table_name):
            raise TableAlreadyExistsError(
                f"Таблица '{table_name}' уже существует."
            )
        self._save_table(table_name, Table(table_name, columns))

    def drop_table(self, table_name: str) -> None:
        if not self._table_exists(table_name):
            raise TableNotFoundError(f"Таблица '{table_name}' не существует.")
        self._delete_table_storage(table_name)

    def has_table(self, table_name: str) -> bool:
        return self._table_exists(table_name)

    def get_table(self, table_name: str) -> Table:
        if not self._table_exists(table_name):
            raise TableNotFoundError(f"Таблица '{table_name}' не существует.")
        return self._load_table(table_name)

    def get_tables(self) -> dict[str, Table]:
        """Вернуть все читаемые таблицы.

        Повреждённые файлы пропускаются, чтобы одна битая таблица не делала
        недоступными все остальные. Каждый пропуск логируется как warning;
        программный список пропущенных таблиц доступен через
        get_corrupted_tables().
        """
        result: dict[str, Table] = {}
        for name in self._list_table_names():
            try:
                result[name] = self._load_table(name)
            except InvalidStorageDataError as error:
                logger.warning(
                    "Пропущена повреждённая таблица '%s': %s", name, error
                )
                continue
        return result

    def get_corrupted_tables(self) -> dict[str, str]:
        """Вернуть имена повреждённых таблиц и текст ошибки для каждой.

        Позволяет UI/CLI сообщить пользователю о недоступных данных вместо
        того, чтобы молча скрывать их из get_tables(). Для реализаций без
        внешнего хранилища (например, in-memory) всегда возвращает {}.
        """
        corrupted: dict[str, str] = {}
        for name in self._list_table_names():
            try:
                self._load_table(name)
            except InvalidStorageDataError as error:
                corrupted[name] = str(error)
        return corrupted

    def insert_record(
        self, table_name: str, record: dict[str, Any]
    ) -> dict[str, Any]:
        table = self.get_table(table_name)
        result = table.insert_record(record)
        self._save_table(table_name, table)
        return result

    def select_records(
        self, table_name: str, **filters: Any
    ) -> list[dict[str, Any]]:
        return self.get_table(table_name).select_records(**filters)

    def update_record(
        self, table_name: str, record_id: int, **updates: Any
    ) -> dict[str, Any]:
        table = self.get_table(table_name)
        result = table.update_record(record_id, **updates)
        self._save_table(table_name, table)
        return result

    def delete_record(self, table_name: str, record_id: int) -> dict[str, Any]:
        table = self.get_table(table_name)
        result = table.delete_record(record_id)
        self._save_table(table_name, table)
        return result

    def sort_records(
        self, table_name: str, field: str, descending: bool = False
    ) -> list[dict[str, Any]]:
        return self.get_table(table_name).sort_records(field, descending)

    # ---------- абстрактные методы хранения ----------

    @abstractmethod
    def _table_exists(self, table_name: str) -> bool:
        """Существует ли таблица в хранилище."""

    @abstractmethod
    def _load_table(self, table_name: str) -> Table:
        """Загрузить таблицу из хранилища (без проверки существования)."""

    @abstractmethod
    def _save_table(self, table_name: str, table: Table) -> None:
        """Сохранить таблицу в хранилище."""

    @abstractmethod
    def _delete_table_storage(self, table_name: str) -> None:
        """Удалить таблицу из хранилища (без проверки существования)."""

    @abstractmethod
    def _list_table_names(self) -> list[str]:
        """Список имён всех таблиц в хранилище."""
