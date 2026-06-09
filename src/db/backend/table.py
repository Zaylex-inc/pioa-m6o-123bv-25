"""Класс таблицы с фиксированным набором колонок."""

from copy import deepcopy
from typing import Any

from .errors import (
    ColumnNotFoundError,
    DuplicateIDError,
    InvalidDataError,
    RecordNotFoundError,
)


class Table:
    """Таблица БД с фиксированным набором колонок."""

    def __init__(self, name: str, columns: tuple[str, ...]):
        if not columns:
            raise InvalidDataError("Таблица должна иметь хотя бы одну колонку.")

        if columns[0] != "id":
            raise InvalidDataError("Первое значение таблицы должно являться id записи.")

        if len(columns) != len(set(columns)):
            raise InvalidDataError("Имена колонок должны быть уникальными.")

        self._name = name
        self._columns = columns
        self._records: list[dict[str, Any]] = []

    def get_name(self) -> str:
        return self._name

    def get_columns(self) -> tuple[str, ...]:
        return self._columns

    def get_records(self) -> list[dict[str, Any]]:
        return deepcopy(self._records)

    def get_record_count(self) -> int:
        return len(self._records)

    def insert_record(self, record: dict[str, Any]) -> dict[str, Any]:
        for column in self._columns:
            if column not in record:
                raise InvalidDataError(f"Отсутствует поле '{column}' в записи.")

        record_id = record["id"]
        if isinstance(record_id, bool) or not isinstance(record_id, int):
            raise InvalidDataError("Тип поля id должен быть int.")

        for column in record:
            if column not in self._columns:
                raise ColumnNotFoundError(
                    f"Поле '{column}' не определено в структуре таблицы."
                )

        if any(r["id"] == record_id for r in self._records):
            raise DuplicateIDError(f"Запись с id={record_id} уже существует.")

        saved_record = deepcopy(record)
        self._records.append(saved_record)
        return deepcopy(saved_record)

    def select_records(self, **filters: Any) -> list[dict[str, Any]]:
        if not filters:
            return deepcopy(self._records)

        for key in filters:
            if key not in self._columns:
                raise ColumnNotFoundError(
                    f"Поле '{key}' не определено в структуре таблицы."
                )

        result: list[dict[str, Any]] = []
        for record in self._records:
            if all(record.get(k) == v for k, v in filters.items()):
                result.append(deepcopy(record))
        return result

    def update_record(self, record_id: int, **updates: Any) -> dict[str, Any]:
        if isinstance(record_id, bool) or not isinstance(record_id, int):
            raise InvalidDataError("Тип поля id должен быть int.")

        if "id" in updates:
            raise InvalidDataError(
                "Поле 'id' нельзя изменять через update_record."
            )

        for key in updates:
            if key not in self._columns:
                raise ColumnNotFoundError(
                    f"Поле '{key}' не определено в структуре таблицы."
                )

        for record in self._records:
            if record.get("id") == record_id:
                for key, value in updates.items():
                    record[key] = value
                return deepcopy(record)

        raise RecordNotFoundError(f"Запись с id={record_id} не найдена.")

    def delete_record(self, record_id: int) -> dict[str, Any]:
        if isinstance(record_id, bool) or not isinstance(record_id, int):
            raise InvalidDataError("Тип поля id должен быть int.")

        for i, record in enumerate(self._records):
            if record.get("id") == record_id:
                deleted = self._records.pop(i)
                return deepcopy(deleted)

        raise RecordNotFoundError(f"Запись с id={record_id} не найдена.")

    def sort_records(
        self, field: str, descending: bool = False
    ) -> list[dict[str, Any]]:
        if field not in self._columns:
            raise ColumnNotFoundError(
                f"Поле '{field}' не определено в структуре таблицы."
            )

        try:
            return sorted(
                deepcopy(self._records),
                key=lambda x: (x.get(field) is None, x.get(field)),
                reverse=descending,
            )
        except TypeError as error:
            raise InvalidDataError(
                f"Невозможно сортировать поле '{field}' — "
                "содержит несравнимые типы данных."
            ) from error
