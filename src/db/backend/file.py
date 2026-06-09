"""Файловая реализация базы данных. Хранит таблицы в JSON-файлах."""

import json
import re
from pathlib import Path
from typing import Any

from .database import Database
from .errors import (
    ColumnNotFoundError,
    DuplicateIDError,
    InvalidDataError,
    InvalidStorageDataError,
    TableNotFoundError,
)
from .table import Table


_VALID_TABLE_NAME = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class FileDatabase(Database):
    """База данных, которая хранит каждую таблицу в отдельном JSON-файле."""

    def __init__(self, directory: str = "data") -> None:
        self._directory = Path(directory).resolve()
        self._directory.mkdir(parents=True, exist_ok=True)

    def _table_exists(self, table_name: str) -> bool:
        return self._get_table_path(table_name).exists()

    def _load_table(self, table_name: str) -> Table:
        path = self._get_table_path(table_name)
        if not path.exists():
            raise TableNotFoundError(f"Таблица '{table_name}' не существует.")

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise InvalidStorageDataError(
                f"Файл таблицы '{table_name}' содержит некорректный JSON."
            ) from error
        except OSError as error:
            raise InvalidStorageDataError(
                f"Не удалось прочитать файл таблицы '{table_name}': {error}"
            ) from error

        return self._deserialize_table(table_name, data)

    def _save_table(self, table_name: str, table: Table) -> None:
        path = self._get_table_path(table_name)
        payload = self._serialize_table(table)
        try:
            with path.open("w", encoding="utf-8") as file:
                json.dump(payload, file, ensure_ascii=False, indent=2)
        except OSError as error:
            raise InvalidStorageDataError(
                f"Не удалось записать файл таблицы '{table_name}': {error}"
            ) from error

    def _delete_table_storage(self, table_name: str) -> None:
        path = self._get_table_path(table_name)
        try:
            path.unlink()
        except OSError as error:
            raise InvalidStorageDataError(
                f"Не удалось удалить файл таблицы '{table_name}': {error}"
            ) from error

    def _list_table_names(self) -> list[str]:
        return sorted(
            p.stem
            for p in self._directory.glob("*.json")
            if p.is_file() and _VALID_TABLE_NAME.match(p.stem)
        )

    def _get_table_path(self, table_name: str) -> Path:
        if not isinstance(table_name, str) or not _VALID_TABLE_NAME.match(table_name):
            raise InvalidDataError(
                f"Недопустимое имя таблицы '{table_name}'. "
                "Разрешены латинские буквы, цифры, '_' и '-', длина 1..64."
            )

        path = (self._directory / f"{table_name}.json").resolve()
        if path.parent != self._directory:
            raise InvalidDataError(
                f"Имя таблицы '{table_name}' выводит путь за пределы каталога хранилища."
            )
        return path

    def _serialize_table(self, table: Table) -> dict[str, Any]:
        return {
            "columns": list(table.get_columns()),
            "records": table.get_records(),
        }

    def _deserialize_table(self, table_name: str, data: Any) -> Table:
        if not isinstance(data, dict):
            raise InvalidStorageDataError(
                f"Файл таблицы '{table_name}' имеет некорректную структуру."
            )
        if "columns" not in data or "records" not in data:
            raise InvalidStorageDataError(
                f"Файл таблицы '{table_name}' не содержит обязательных полей "
                "'columns' и 'records'."
            )
        if not isinstance(data["columns"], list) or not isinstance(data["records"], list):
            raise InvalidStorageDataError(
                f"Файл таблицы '{table_name}': 'columns' и 'records' "
                "должны быть списками."
            )

        for index, column in enumerate(data["columns"]):
            if not isinstance(column, str) or not column:
                raise InvalidStorageDataError(
                    f"Файл таблицы '{table_name}': имя колонки с индексом "
                    f"{index} должно быть непустой строкой (получено: {column!r})."
                )

        columns = tuple(data["columns"])
        try:
            table = Table(table_name, columns)
        except InvalidDataError as error:
            raise InvalidStorageDataError(
                f"Файл таблицы '{table_name}': некорректный набор колонок: {error}"
            ) from error

        for record in data["records"]:
            if not isinstance(record, dict):
                raise InvalidStorageDataError(
                    f"Файл таблицы '{table_name}': запись должна быть объектом."
                )
            try:
                table.insert_record(record)
            except (InvalidDataError, DuplicateIDError, ColumnNotFoundError) as error:
                raise InvalidStorageDataError(
                    f"Файл таблицы '{table_name}': некорректная запись "
                    f"{record!r}: {error}"
                ) from error
        return table
