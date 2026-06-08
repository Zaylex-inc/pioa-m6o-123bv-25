"""Пользовательские исключения для системы управления БД."""


class DatabaseError(Exception):
    """Базовый класс для всех ошибок БД."""
    pass


class TableNotFoundError(DatabaseError):
    """Таблица не найдена."""
    pass


class TableAlreadyExistsError(DatabaseError):
    """Таблица с таким именем уже существует."""
    pass


class DuplicateIDError(DatabaseError):
    """Запись с таким id уже существует в таблице."""
    pass


class RecordNotFoundError(DatabaseError):
    """Запись с указанным id не найдена."""
    pass


class ColumnNotFoundError(DatabaseError):
    """Колонка не определена в структуре таблицы."""
    pass


class InvalidDataError(DatabaseError):
    """Некорректные данные: тип id, структура колонок, несравнимые значения и т.п."""
    pass
