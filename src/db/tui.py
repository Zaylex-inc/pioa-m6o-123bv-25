from .backend.memory import Database, Table

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
                print(" Ошибка: введите целое число.")
    
    def _read_positive_int(self, prompt: str) -> int:
    
        while True:
            value = self._read_int(prompt)
            if value > 0:
                return value
            print(" Ошибка: введите число больше 0.")
    
    def _print_header(self, title: str) -> None:
       
        print("\n" + "=" * 50)
        print(f" {title}")
        print("=" * 50)
    
    def _print_success(self, message: str) -> None:
  
        print(f" {message}")
    
    def _print_error(self, message: str) -> None:
       
        print(f" {message}")
    
    def _print_info(self, message: str) -> None:
       
        print(f" {message}")
    
    def show_tables(self) -> None:
        self._print_header("СПИСОК ТАБЛИЦ")
        if not self.db.tables:
            self._print_info("База данных пуста. Нет созданных таблиц.")
            return
        
        print(f"\nВсего таблиц: {len(self.db.tables)}\n")
        
        for i, (table_name, table) in enumerate(self.db.tables.items(), 1):
            print(f"{i}. {table_name}")
            print(f"   Колонки: {', '.join(table.columns)}")
            print(f"   Записей: {len(table.records)}")
            print()
    
    def show_table_info(self) -> None:
        
        self._print_header("ИНФОРМАЦИЯ О ТАБЛИЦЕ")
        
        table_name = input("Введите имя таблицы: ").strip()
        
        if table_name not in self.db.tables:
            self._print_error(f"Таблица '{table_name}' не существует.")
            return
        
        table = self.db.tables[table_name]
        
        print(f"\n Таблица: {table_name}")
        print(f" Колонки ({len(table.columns)}): {', '.join(table.columns)}")
        print(f" Количество записей: {len(table.records)}")
        
        if table.records:
            print(f"\n Пример записи:")
            print(f"   {table.records[0]}")
    
    def create_table(self) -> None:
        
        self._print_header("СОЗДАНИЕ ТАБЛИЦЫ")
        
        table_name = input("Введите имя таблицы: ").strip()
        
        if not table_name:
            self._print_error("Имя таблицы не может быть пустым.")
            return
        
        columns_input = input("Введите названия колонок через запятую (первая должна быть 'id'): ").strip()
        columns = tuple(col.strip() for col in columns_input.split(','))
        
        if not columns:
            self._print_error("Таблица должна иметь хотя бы одну колонку.")
            return
        
        try:
            self.db.create_table(table_name, columns)
            self._print_success(f"Таблица '{table_name}' успешно создана!")
        except ValueError as e:
            self._print_error(str(e))
    
    def insert_record(self) -> None:
        
        self._print_header("ВСТАВКА ЗАПИСИ")
        
        table_name = input("Введите имя таблицы: ").strip()
        
        if table_name not in self.db.tables:
            self._print_error(f"Таблица '{table_name}' не существует.")
            return
        
        table = self.db.tables[table_name]
        record = {}
        
        self._print_info(f"Заполните поля таблицы '{table_name}':")
        
        for column in table.columns:
            while True:
                value = input(f"  {column}: ").strip()
                
                if column == "id":
                    try:
                        value = int(value)
                        for existing in table.records:
                            if existing.get("id") == value:
                                self._print_error(f"ID {value} уже существует!")
                                break
                        else:
                            record[column] = value
                            break
                    except ValueError:
                        self._print_error("ID должен быть целым числом!")
                        continue
                else:
                
                    record[column] = value
                    break
        
        try:
            self.db.insert_record(table_name, record)
            self._print_success("Запись успешно добавлена!")
        except ValueError as e:
            self._print_error(str(e))
    
    def select_records(self) -> None:
        
        self._print_header("ВЫБОРКА ЗАПИСЕЙ")
        
        table_name = input("Введите имя таблицы: ").strip()
        
        if table_name not in self.db.tables:
            self._print_error(f"Таблица '{table_name}' не существует.")
            return
        
       
        use_filters = input("Добавить фильтры? (y/n): ").strip().lower()
        filters = {}
        
        if use_filters == 'y':
            self._print_info("Введите фильтры (пустая строка для завершения):")
            while True:
                key = input("  Поле: ").strip()
                if not key:
                    break
                value = input("  Значение: ").strip()
                if value.isdigit():
                    value = int(value)
                filters[key] = value
        
        try:
            records = self.db.select_records(table_name, **filters)
            
            print(f"\n Найдено записей: {len(records)}\n")
            
            if records:
                for i, record in enumerate(records, 1):
                    print(f"{i}. {record}")
            else:
                self._print_info("Записей, соответствующих фильтрам, не найдено.")
                
        except ValueError as e:
            self._print_error(str(e))
    
    def update_record(self) -> None:
        
        self._print_header("ОБНОВЛЕНИЕ ЗАПИСИ")
        
        table_name = input("Введите имя таблицы: ").strip()
        
        if table_name not in self.db.tables:
            self._print_error(f"Таблица '{table_name}' не существует.")
            return
        
        record_id = self._read_int("Введите ID записи для обновления: ")
        
        
        table = self.db.tables[table_name]
        record_exists = False
        for record in table.records:
            if record.get("id") == record_id:
                record_exists = True
                break
        
        if not record_exists:
            self._print_error(f"Запись с ID {record_id} не найдена.")
            return
        
        self._print_info(f"Введите поля для обновления (пустая строка для завершения):")
        updates = {}
        
        for column in table.columns:
            if column == "id":
                continue  
            value = input(f"  Новое значение для {column} (Enter - пропустить): ").strip()
            if value:
                updates[column] = value
        
        if not updates:
            self._print_info("Нет полей для обновления.")
            return
        
        updates["id"] = record_id
        
        try:
            updated_record = self.db.update_record(table_name, **updates)
            self._print_success("Запись успешно обновлена!")
            print(f"Обновлённая запись: {updated_record}")
        except ValueError as e:
            self._print_error(str(e))
    
    def delete_record(self) -> None:
       
        self._print_header("УДАЛЕНИЕ ЗАПИСИ")
        
        table_name = input("Введите имя таблицы: ").strip()
        
        if table_name not in self.db.tables:
            self._print_error(f"Таблица '{table_name}' не существует.")
            return
        
        record_id = self._read_int("Введите ID записи для удаления: ")
        
        
        confirm = input(f"Вы уверены, что хотите удалить запись с ID {record_id}? (y/n): ").strip().lower()
        
        if confirm != 'y':
            self._print_info("Удаление отменено.")
            return
        
        try:
            deleted_record = self.db.delete_record(table_name, record_id)
            self._print_success("Запись успешно удалена!")
            print(f"Удалённая запись: {deleted_record}")
        except ValueError as e:
            self._print_error(str(e))
    
    def drop_table(self) -> None:
        self._print_header("УДАЛЕНИЕ ТАБЛИЦЫ")
        
        if not self.db.tables:
            self._print_info("Нет таблиц для удаления.")
            return
        
        
        print("Существующие таблицы:")
        for name in self.db.tables.keys():
            print(f"  - {name}")
        
        table_name = input("\nВведите имя таблицы для удаления: ").strip()
        
        if table_name not in self.db.tables:
            self._print_error(f"Таблица '{table_name}' не существует.")
            return
        
      
        confirm = input(f"Вы уверены, что хотите удалить таблицу '{table_name}'? (y/n): ").strip().lower()
        
        if confirm != 'y':
            self._print_info("Удаление отменено.")
            return
        
        try:
            self.db.drop_table(table_name)
            self._print_success(f"Таблица '{table_name}' успешно удалена!")
        except ValueError as e:
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
        print("8. Удалить таблицу")
        print("0. Выход")
        print("=" * 50)
    
    def run(self) -> None:
        self._print_success("Добро пожаловать в систему управления базой данных!")
        
        while self.running:
            self.show_main_menu()
            
            choice = self._read_int("Выберите действие: ")
            
            if choice == 1:
                self.show_tables()
            elif choice == 2:
                self.show_table_info()
            elif choice == 3:
                self.create_table()
            elif choice == 4:
                self.insert_record()
            elif choice == 5:
                self.select_records()
            elif choice == 6:
                self.update_record()
            elif choice == 7:
                self.delete_record()
            elif choice == 8:
                self.drop_table()
            elif choice == 0:
                self._print_success("До свидания!")
                self.running = False
            else:
                self._print_error("Неверный выбор. Пожалуйста, выберите действие от 0 до 8.")
        
        print("\n Программа завершена.")
