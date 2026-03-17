from .backend.memory import (
    create_author, select_authors, update_author, delete_author,
    create_book, select_books, update_book, delete_book
)
# ---------- Вспомогательные функции ввода ----------

def _read_int(prompt: str) -> int:
    """Запрашивает у пользователя целое число. Повторяет до успеха."""
    while True:
        raw = input(prompt).strip()
        try:
            return int(raw)
        except ValueError:
            print("Ошибка: введите целое число.")


def _read_optional_int(prompt: str) -> int | None:
    """
    Запрашивает целое число. Если пользователь вводит пустую строку,
    возвращает None (поле не задано).
    """
    while True:
        raw = input(prompt).strip()
        if raw == "":
            return None
        try:
            return int(raw)
        except ValueError:
            print("Ошибка: введите целое число или оставьте поле пустым.")


def _read_nonempty_string(prompt: str) -> str:
    """Запрашивает непустую строку. Повторяет, пока не будет введено что-то."""
    while True:
        s = input(prompt).strip()
        if s:
            return s
        print("Ошибка: значение не может быть пустым.")


# ---------- Функции вывода (таблицы) ----------

def _print_authors(author_list: list) -> None:
    """Выводит список авторов в виде таблицы."""
    if not author_list:
        print("Авторы не найдены.")
        return
    print(f"{'ID'} | {'Имя'} | {'Страна'}")
    print("-" * 45)
    for a in author_list:
        print(f"{a[0]} | {a[1]} | {a[2]}")


def _print_books(book_list: list) -> None:
    """Выводит список книг в виде таблицы."""
    if not book_list:
        print("Книги не найдены.")
        return
    print(f"{'ID'} | {'Название'} | {'Автор ID'} | {'Год'} | {'Жанр'}")
    print("-" * 65)
    for b in book_list:
        #
        print(f"{b[0]} | {b[1]} | {b[2]} | {b[3]} | {b[4]}")


# ---------- Функции для работы с авторами ----------

def _add_author() -> None:
    """Диалог добавления нового автора."""
    print("\n--- Добавление автора ---")
    author_id = _read_int("ID автора (целое число): ")
    name = _read_nonempty_string("Имя автора: ")
    country = input("Страна: ").strip()  
    try:
        new = create_author(author_id, name, country)
        print("Автор успешно добавлен:")
        _print_authors([new])
    except ValueError as e:
        print(f"Ошибка: {e}")


def _find_authors() -> None:
    """Диалог поиска авторов с фильтрами."""
    print("\n--- Поиск авторов ---")
    print("Введите критерии поиска (пустое поле = пропустить фильтр):")
    author_id = _read_optional_int("ID автора: ")
    name = input("Имя автора: ").strip() or None
    country = input("Страна: ").strip() or None
    results = select_authors(author_id, name, country)
    _print_authors(results)


def _update_author() -> None:
    """Диалог обновления данных автора."""
    print("\n--- Обновление автора ---")
    author_id = _read_int("Введите ID автора для обновления: ")
    print("Введите новые значения (если оставить пустым, значение не изменится):")
    name = input("Новое имя: ").strip() or None
    country = input("Новая страна: ").strip() or None
    try:
        updated = update_author(author_id, name, country)
        print("Автор обновлён:")
        _print_authors([updated])
    except ValueError as e:
        print(f"Ошибка: {e}")


def _delete_author() -> None:
    """Диалог удаления автора."""
    print("\n--- Удаление автора ---")
    author_id = _read_int("Введите ID автора для удаления: ")
    try:
        deleted = delete_author(author_id)
        print("Автор удалён:")
        _print_authors([deleted])
    except ValueError as e:
        print(f"Ошибка: {e}")


def _show_all_authors() -> None:
    """Выводит всех авторов."""
    all_authors = select_authors()  
    _print_authors(all_authors)


# ---------- Функции для работы с книгами ----------

def _add_book() -> None:
    """Диалог добавления новой книги."""
    print("\n--- Добавление книги ---")
    book_id = _read_int("ID книги: ")
    title = _read_nonempty_string("Название: ")
    author_id = _read_int("ID автора: ")
    year = _read_int("Год издания: ")
    genre = input("Жанр: ").strip()  
    try:
        new = create_book(book_id, title, author_id, year, genre)
        print("Книга успешно добавлена:")
        _print_books([new])
    except ValueError as e:
        print(f"Ошибка: {e}")


def _find_books() -> None:
    """Диалог поиска книг с фильтрами."""
    print("\n--- Поиск книг ---")
    print("Введите критерии поиска (пустое поле = пропустить фильтр):")
    book_id = _read_optional_int("ID книги: ")
    title = input("Название: ").strip() or None
    author_id = _read_optional_int("ID автора: ")
    year = _read_optional_int("Год издания: ")
    genre = input("Жанр: ").strip() or None
    results = select_books(book_id, title, author_id, year, genre)
    _print_books(results)


def _update_book() -> None:
    """Диалог обновления данных книги."""
    print("\n--- Обновление книги ---")
    book_id = _read_int("Введите ID книги для обновления: ")
    print("Введите новые значения (если оставить пустым, значение не изменится):")
    title = input("Новое название: ").strip() or None
    author_id = _read_optional_int("Новый ID автора: ")
    year = _read_optional_int("Новый год издания: ")
    genre = input("Новый жанр: ").strip() or None
    try:
        updated = update_book(book_id, title, author_id, year, genre)
        print("Книга обновлена:")
        _print_books([updated])
    except ValueError as e:
        print(f"Ошибка: {e}")


def _delete_book() -> None:
    """Диалог удаления книги."""
    print("\n--- Удаление книги ---")
    book_id = _read_int("Введите ID книги для удаления: ")
    try:
        deleted = delete_book(book_id)
        print("Книга удалена:")
        _print_books([deleted])
    except ValueError as e:
        print(f"Ошибка: {e}")


def _show_all_books() -> None:
    """Выводит все книги."""
    all_books = select_books()  
    _print_books(all_books)


# ---------- Меню ----------

def _authors_menu() -> None:
    """Меню операций с авторами."""
    while True:
        print("\n--- Меню авторов ---")
        print("1. Добавить автора")
        print("2. Найти авторов")
        print("3. Обновить автора")
        print("4. Удалить автора")
        print("5. Показать всех авторов")
        print("0. Назад в главное меню")
        choice = input("Выберите действие: ").strip()

        if choice == "1":
            _add_author()
        elif choice == "2":
            _find_authors()
        elif choice == "3":
            _update_author()
        elif choice == "4":
            _delete_author()
        elif choice == "5":
            _show_all_authors()
        elif choice == "0":
            break
        else:
            print("Неверный ввод. Пожалуйста, выберите пункт из меню.")


def _books_menu() -> None:
    """Меню операций с книгами."""
    while True:
        print("\n--- Меню книг ---")
        print("1. Добавить книгу")
        print("2. Найти книги")
        print("3. Обновить книгу")
        print("4. Удалить книгу")
        print("5. Показать все книги")
        print("0. Назад в главное меню")
        choice = input("Выберите действие: ").strip()

        if choice == "1":
            _add_book()
        elif choice == "2":
            _find_books()
        elif choice == "3":
            _update_book()
        elif choice == "4":
            _delete_book()
        elif choice == "5":
            _show_all_books()
        elif choice == "0":
            break
        else:
            print("Неверный ввод. Пожалуйста, выберите пункт из меню.")


def run() -> None:
    """
    Главная функция запуска интерфейса.
    Выводит основное меню и обрабатывает выбор пользователя.
    """
    while True:
        print("\n=== База данных 'Книги и авторы' (in-memory) ===")
        print("1. Работа с авторами")
        print("2. Работа с книгами")
        print("0. Выход")
        choice = input("Выберите раздел: ").strip()

        if choice == "1":
            _authors_menu()
        elif choice == "2":
            _books_menu()
        elif choice == "0":
            print("Выход из программы.")
            break
        else:
            print("Неверный ввод. Повторите.")