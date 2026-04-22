from typing import Any


class Table:
  

    def __init__(self, columns: tuple[str, ...]):
        self.columns = columns
        self.records: list[dict[str, Any]] = []

    def insert_record(self, record: dict[str, Any]) -> None:
        if type(record["id"]) is not int:
            raise ValueError("Тип поля id должен быть int")

        for column in self.columns:
            if column not in record:
                raise ValueError(f"Отсутствует поле '{column}' в записи.")

        for column in record:
            if column not in self.columns:
                raise ValueError(f"Поле '{column}' не определено в структуре таблицы.")

        self.records.append(record)

    def select_records(self, **filters: Any) -> list[dict[str, Any]]:
        if not filters:
            return self.records.copy()

        result: list[dict[str, Any]] = []

        for record in self.records:
            match = True
            for key, value in filters.items():
                if key not in self.columns:
                    raise ValueError(f"Поле '{key}' не определено в структуре таблицы.")
                if record.get(key) != value:
                    match = False
                    break

            if match:
                result.append(record)

        return result

    def update_record(self, **updates) -> dict[str, Any]:
        for record in self.records:
            if record.get("id") == updates.get("id"):
                for key, value in updates.items():
                    if key not in self.columns:
                        raise ValueError(
                            f"Поле '{key}' не определено в структуре таблицы."
                        )
                    record[key] = value
                return record

        raise ValueError(f"Запись с id {updates.get('id')} не найдена")

    def delete_record(self, id: int) -> dict[str, Any]:
        for i, record in enumerate(self.records):
            if record.get("id") == id:
                deleted_record = self.records.pop(i)  # pop удаляет и возвращает элемент
                return deleted_record

        raise ValueError(f"Запись с id {id} не найдена")


class Database:
    def __init__(self):
        # Словарь таблиц базы данных.
        self.tables: dict[str, Table] = {}

    def create_table(self, table_name: str, columns: tuple[str, ...]) -> None:
        if table_name in self.tables:
            raise ValueError(f"Таблица '{table_name}' уже существует.")

        if columns[0] != "id":
            raise ValueError("Первое значение таблицы должно являться id записи")

        self.tables[table_name] = Table(columns)

    def insert_record(self, table_name: str, record: dict[str, Any]) -> None:
        
        if table_name not in self.tables:
            raise ValueError(f"Таблица '{table_name}' не существует.")

        self.tables[table_name].insert_record(record)

    def select_records(self, table_name: str, **filters: Any) -> list[dict[str, Any]]:
        if table_name not in self.tables:
            raise ValueError(f"Таблица '{table_name}' не существует.")

        return self.tables[table_name].select_records(**filters)

    def update_record(self, table_name: str, **updates) -> dict[str, Any]:
        if table_name not in self.tables:
            raise ValueError(f"Таблица '{table_name}' не существует.")

        return self.tables[table_name].update_record(**updates)

    def delete_record(self, table_name: str, id: int) -> dict[str, Any]:
        if table_name not in self.tables:
            raise ValueError(f"Таблица '{table_name}' не существует.")
        return self.tables[table_name].delete_record(id)

    def drop_table(self, table_name: str) -> None:
        if table_name not in self.tables:
            raise ValueError(f"Таблица '{table_name}' не существует.")
        del self.tables[table_name]
