"""In-memory реализация базы данных.

Данные живут только во время работы программы.
Для обратной совместимости со старыми тестами и кодом экспортирует:
  - `MemoryDatabase` — новое имя
  - `Database` — алиас, равный `MemoryDatabase`
  - `Table` — реэкспорт из table.py
"""

from .database import Database as _AbstractDatabase
from .errors import TableNotFoundError
from .table import Table  # реэкспорт для обратной совместимости


class MemoryDatabase(_AbstractDatabase):
    """База данных, хранящая таблицы в оперативной памяти."""

    def __init__(self) -> None:
        self._tables: dict[str, Table] = {}

    def _table_exists(self, table_name: str) -> bool:
        return table_name in self._tables

    def _load_table(self, table_name: str) -> Table:
        if table_name not in self._tables:
            raise TableNotFoundError(f"Таблица '{table_name}' не существует.")
        return self._tables[table_name]

    def _save_table(self, table_name: str, table: Table) -> None:
        self._tables[table_name] = table

    def _delete_table_storage(self, table_name: str) -> None:
        del self._tables[table_name]

    def _list_table_names(self) -> list[str]:
        return list(self._tables.keys())


# Алиас для обратной совместимости — старые тесты импортируют `Database`.
Database = MemoryDatabase

__all__ = ["MemoryDatabase", "Database", "Table"]
