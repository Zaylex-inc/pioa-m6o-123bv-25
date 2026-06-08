from .backend.memory import Database, Table
from .backend.errors import (
    DatabaseError,
    TableNotFoundError,
    DuplicateIDError,
    RecordNotFoundError,
    ColumnNotFoundError,
    InvalidDataError,
)


class TUI:
    def __init__(self):
        self.db = Database()
        self.running = True

    def _read_int(self, prompt: str) -> int:
        while True:
            raw = input(prompt).strip()
            try:
                return int(raw)
            except ValueError:
                self._print_error("Ошибка: введите целое число.")

    def _read_positive_int(self, prompt: str) -> int:
        while True:
            value = self._read_int(prompt)
            if value > 0:
                return value
            self._print_error("Ошибка: введите число больше 0.")

    def _try_convert(self, value: str):
        """Попытаться преобразовать строку в int, float или оставить строкой."""
        value = value.strip()
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            return value

    def _print_header(self, title: str) -> None:
        print("\n" + "=" * 50)
        print(f" {title}")
        print("=" * 50)

    def _print_success(self, message: str) -> None:
        print(f" ✓ {message}")

    def _print_error(self, message: str) -> None:
        print(f" ✗ {message}")

    def _print_info(self, message: str) -> None:
        print(f" ℹ {message}")

    def show_tables(self) -> None:
        self._print_header("СПИСОК ТАБЛИЦ")
        try:
            tables = self.db.get_tables()
            if not tables:
                self._print_info("База данных пуста. Нет созданных таблиц.")
                return

            print(f"\nВсего таблиц: {len(tables)}\n")

            for i, (table_name, table) in enumerate(tables.items(), 1):
                print(f"{i}. {table_name}")
                print(f"   Колонки: {', '.join(table.get_columns())}")
                print(f"   Записей: {table.get_record_count()}")
                print()
        except DatabaseError as e:
            self._print_error(str(e))

    def show_table_info(self) -> None:
        self._print_header("ИНФОРМАЦИЯ О ТАБЛИЦЕ")

        table_name = input("Введите имя таблицы: ").strip()

        try:
            table = self.db.get_table(table_name)

            print(f"\n Таблица: {table_name}")
            print(f" Колонки ({len(table.get_columns())}): {', '.join(table.get_columns())}")
            print(f" Количество записей: {table.get_record_count()}")

            records = table.get_records()
            if records:
                print(f"\n Пример записи:")
                print(f"   {records[0]}")
        except TableNotFoundError as e:
            self._print_error(str(e))
        except DatabaseError as e:
            self._print_error(str(e))

    def create_table(self) -> None:
        self._print_header("СОЗДАНИЕ ТАБЛИЦЫ")

        table_name = input("Введите имя таблицы: ").strip()

        if not table_name:
            self._print_error("Имя таблицы не может быть пустым.")
            return

        columns_input = input("Введите названия колонок через запятую (первая должна быть 'id'): ").strip()
        columns = tuple(col.strip() for col in columns_input.split(',') if col.strip())

        try:
            self.db.create_table(table_name, columns)
            self._print_success(f"Таблица '{table_name}' успешно создана!")
        except InvalidDataError as e:
            self._print_error(str(e))
        except DatabaseError as e:
            self._print_error(str(e))

    def insert_record(self) -> None:
        self._print_header("ВСТАВКА ЗАПИСИ")

        table_name = input("Введите имя таблицы: ").strip()

        try:
            table = self.db.get_table(table_name)
            columns = table.get_columns()
            record = {}

            self._print_info(f"Заполните поля таблицы '{table_name}':")

            for column in columns:
                while True:
                    value = input(f"  {column}: ").strip()

                    if column == "id":
                        try:
                            value = int(value)
                            record[column] = value
                            break
                        except ValueError:
                            self._print_error("ID должен быть целым числом!")
                            continue
                    else:
                        record[column] = self._try_convert(value)
                        break

            self.db.insert_record(table_name, record)
            self._print_success("Запись успешно добавлена!")
        except TableNotFoundError as e:
            self._print_error(str(e))
        except DuplicateIDError as e:
            self._print_error(str(e))
        except InvalidDataError as e:
            self._print_error(str(e))
        except DatabaseError as e:
            self._print_error(str(e))

    def select_records(self) -> None:
        self._print_header("ВЫБОРКА ЗАПИСЕЙ")

        table_name = input("Введите имя таблицы: ").strip()

        try:
            table = self.db.get_table(table_name)

            use_filters = input("Добавить фильтры? (y/n): ").strip().lower()
            filters = {}

            if use_filters == 'y':
                self._print_info("Введите фильтры (пустая строка для завершения):")
                while True:
                    key = input("  Поле: ").strip()
                    if not key:
                        break
                    value = input("  Значение: ").strip()
                    filters[key] = self._try_convert(value)

            records = self.db.select_records(table_name, **filters)

            print(f"\n Найдено записей: {len(records)}\n")

            if records:
                for i, record in enumerate(records, 1):
                    print(f"{i}. {record}")
            else:
                self._print_info("Записей, соответствующих фильтрам, не найдено.")

        except TableNotFoundError as e:
            self._print_error(str(e))
        except ColumnNotFoundError as e:
            self._print_error(str(e))
        except DatabaseError as e:
            self._print_error(str(e))

    def update_record(self) -> None:
        self._print_header("ОБНОВЛЕНИЕ ЗАПИСИ")

        table_name = input("Введите имя таблицы: ").strip()

        try:
            table = self.db.get_table(table_name)
            record_id = self._read_int("Введите ID записи для обновления: ")

            self._print_info(f"Введите поля для обновления (пустая строка для завершения):")
            updates = {}

            for column in table.get_columns():
                if column == "id":
                    continue
                value = input(f"  Новое значение для {column} (Enter - пропустить): ").strip()
                if value:
                    updates[column] = self._try_convert(value)

            if not updates:
                self._print_info("Нет полей для обновления.")
                return

            updated_record = self.db.update_record(table_name, record_id, **updates)
            self._print_success("Запись успешно обновлена!")
            print(f"Обновлённая запись: {updated_record}")
        except TableNotFoundError as e:
            self._print_error(str(e))
        except RecordNotFoundError as e:
            self._print_error(str(e))
        except ColumnNotFoundError as e:
            self._print_error(str(e))
        except InvalidDataError as e:
            self._print_error(str(e))
        except DatabaseError as e:
            self._print_error(str(e))

    def delete_record(self) -> None:
        self._print_header("УДАЛЕНИЕ ЗАПИСИ")

        table_name = input("Введите имя таблицы: ").strip()

        try:
            table = self.db.get_table(table_name)
            record_id = self._read_int("Введите ID записи для удаления: ")

            confirm = input(f"Вы уверены, что хотите удалить запись с ID {record_id}? (y/n): ").strip().lower()

            if confirm != 'y':
                self._print_info("Удаление отменено.")
                return

            deleted_record = self.db.delete_record(table_name, record_id)
            self._print_success("Запись успешно удалена!")
            print(f"Удалённая запись: {deleted_record}")
        except TableNotFoundError as e:
            self._print_error(str(e))
        except RecordNotFoundError as e:
            self._print_error(str(e))
        except DatabaseError as e:
            self._print_error(str(e))

    def sort_records(self) -> None:
        self._print_header("СОРТИРОВКА ЗАПИСЕЙ")

        table_name = input("Введите имя таблицы: ").strip()

        try:
            table = self.db.get_table(table_name)
            columns = table.get_columns()

            print(f"Доступные колонки: {', '.join(columns)}")
            field = input("Введите поле для сортировки: ").strip()

            direction = input("Направление (asc/desc): ").strip().lower()
            descending = direction == 'desc'

            records = self.db.sort_records(table_name, field, descending)

            print(f"\n Отсортировано записей: {len(records)}\n")

            if records:
                for i, record in enumerate(records, 1):
                    print(f"{i}. {record}")
            else:
                self._print_info("Нет записей для сортировки.")

        except TableNotFoundError as e:
            self._print_error(str(e))
        except ColumnNotFoundError as e:
            self._print_error(str(e))
        except InvalidDataError as e:
            self._print_error(str(e))
        except DatabaseError as e:
            self._print_error(str(e))

    def drop_table(self) -> None:
        self._print_header("УДАЛЕНИЕ ТАБЛИЦЫ")

        try:
            tables = self.db.get_tables()
            if not tables:
                self._print_info("Нет таблиц для удаления.")
                return

            print("Существующие таблицы:")
            for name in tables.keys():
                print(f"  - {name}")

            table_name = input("\nВведите имя таблицы для удаления: ").strip()

            confirm = input(f"Вы уверены, что хотите удалить таблицу '{table_name}'? (y/n): ").strip().lower()

            if confirm != 'y':
                self._print_info("Удаление отменено.")
                return

            self.db.drop_table(table_name)
            self._print_success(f"Таблица '{table_name}' успешно удалена!")
        except TableNotFoundError as e:
            self._print_error(str(e))
        except DatabaseError as e:
            self._print_error(str(e))

    def show_main_menu(self) -> None:
        print("\n" + "=" * 50)
        print("         УПРАВЛЕНИЕ БАЗОЙ ДАННЫХ")
        print("=" * 50)
        print("1. Показать все таблицы")
        print("2. Информация о таблице")
        print("3. Создать таблицу")
        print("4. Вставить запись")
        print("5. Выбрать записи")
        print("6. Обновить запись")
        print("7. Удалить запись")
        print("8. Сортировать записи")
        print("9. Удалить таблицу")
        print("0. Выход")
        print("=" * 50)

    def run(self) -> None:
        self._print_success("Добро пожаловать в систему управления базой данных!")

        actions = {
            1: self.show_tables,
            2: self.show_table_info,
            3: self.create_table,
            4: self.insert_record,
            5: self.select_records,
            6: self.update_record,
            7: self.delete_record,
            8: self.sort_records,
            9: self.drop_table,
            0: lambda: setattr(self, 'running', False),
        }

        while self.running:
            self.show_main_menu()

            choice = self._read_int("Выберите действие: ")

            if choice in actions:
                if choice == 0:
                    self._print_success("До свидания!")
                    actions[choice]()
                else:
                    actions[choice]()
            else:
                self._print_error("Неверный выбор. Пожалуйста, выберите действие от 0 до 9.")

        print("\n Программа завершена.")