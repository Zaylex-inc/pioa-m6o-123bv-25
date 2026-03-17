

type AuthorRecord = tuple[int, str, str]  # (author_id, name, country)
type BookRecord = tuple[int, str, int, int, str]  # (book_id, title, author_id, published_date, genre)

Authors: list[AuthorRecord] = []
Books: list[BookRecord] = []

def create_author(
    author_id: int, name: str, country: str
) -> AuthorRecord:
    
    """
    Создаёт нового автора и добавляет в таблицу Authors.
    Возвращает созданную запись.
    При ошибках выбрасывает ValueError.
    """
    
    if  author_id< 0:
        raise ValueError("ID должен быть неотрицательным числом.")
    
    if any(record[0] == author_id for record in Authors):
       raise ValueError(f'Автор с таким ID = {author_id} уже существует.')
    
    if not name.strip():
        raise ValueError("Имя автора не может быть пустым.")
    
    
    
    new_record: AuthorRecord = (
        author_id,
        name.strip(),
        country.strip()
    )
    
    Authors.append(new_record)
    
    return new_record
    



def select_authors(
    author_id: int | None = None,
    name:str | None=None,
    country: str | None = None
) -> list[AuthorRecord]:
    
    """
    Выполняет выборку записей из таблицы Authors
    в соответствии с переданными фильтрами.

    Если фильтры не заданы, возвращается копия всей таблицы.
    """
    
    if (
        author_id is None
        and name is None
        and country is None
    ):
        return Authors.copy()
    
    results: list[AuthorRecord] = []
    
    for record in Authors:
        if author_id is not None and record[0]!= author_id:
            continue
        if name is not None and record[1]!=name:
            continue
        if country is not None and record[2]!=country:
            continue
        results.append(record)
    return results
        
        
       

def update_author(
    author_id: int,
    name: str | None = None,
    country: str |None = None
) -> AuthorRecord:
    
    """
    Обновляет данные автора с указанным id.
    Возвращает обновлённую запись.
    Если автор не найден, выбрасывает ValueError.
    """
    
    index = None
    for i, record in enumerate(Authors):
        if record[0] == author_id:
            index = i
            break
    if index is None:
        raise ValueError(f'Автор с ID = {author_id} не найден.')
    
    current_record: AuthorRecord = Authors[index]
    new_name: str = name.strip() if name is not None else current_record[1]
    new_country: str = country.strip() if country is not None else current_record[2]
   
    if name is not None and new_name == "":
        raise ValueError("Имя автора не может быть пустым.")
    
    updated: AuthorRecord =(
        author_id,
        new_name,
        new_country
    )
    
    Authors[index] = updated
    
    return updated
    
    


def delete_author(
    author_id: int,
) -> AuthorRecord:
    """
    Удаляет автора с указанным id.
    Возвращает удалённую запись.
    Если автор не найден, выбрасывает ValueError.
    """
    
    
    if any(b[2] == author_id for b in Books):
        raise ValueError(f'Нельзя удалить автора с id={author_id}, так как у него есть книги. Сначала удалите книги.')
        
    
    for i, record in enumerate(Authors):
        if record[0] == author_id:
            delete_AuthorRecord = Authors.pop(i)
            return delete_AuthorRecord

    raise ValueError(f"Автор с id={author_id} не найден.")
def _author_exists(
    author_id: int
) -> bool:
    """Возвращает True, если автор с указанным id существует."""
    for id in Authors:
        if author_id == id[0]:
            return True
    return False 
        
def create_book (
    book_id: int, 
    title: str, 
    author_id: int, 
    published_date: int, 
    genre: str
) -> BookRecord:
    """
    Добавляет новую книгу в таблицу books.
    Проверяет уникальность book_id, существование автора,
    корректность года и непустое название.
    Возвращает созданную запись.
    """
    if not _author_exists(author_id):
        raise ValueError(f'Автор с id={author_id} не существует. Сначала создайте автора.')
    
    if book_id < 0:
        raise ValueError('ID книги должен быть положительным числом.')
    
    for record in Books:
        if book_id == record[0]:
            raise ValueError(f'Книга с ID={book_id} уже существует')
        
    if not title.strip():
        raise ValueError("Название книги не может быть пустым.")
    
    new_book: BookRecord = (
        book_id,
        title.strip(),
        author_id,
        published_date,
        genre.strip()
    )
    Books.append(new_book)
    return new_book


def select_books(
    book_id: int | None = None, 
    title: str | None = None, 
    author_id: int | None = None, 
    published_date: int | None = None, 
    genre: str | None = None
) -> list[BookRecord]:
    """
    Возвращает список книг, соответствующих всем переданным фильтрам.
    Если фильтров нет, возвращает копию всей таблицы.
    """
    if(
        book_id is None 
        and title is None
        and author_id is None 
        and published_date is None
        and genre is None
    ):
        return Books.copy()
    
    results: list[BookRecord] = []
    for record in Books:
        if book_id is not None and record[0]!=book_id:
            continue 
        if title is not None and record[1]!=title:
            continue 
        if author_id is not None and record[2]!=author_id:
            continue 
        if published_date is not None and record[3]!=published_date:
            continue 
        if genre is not None and record[4]!=genre:
            continue 
        results.append(record)
    return results

def update_book(
    book_id: int,
    title: str | None = None,
    author_id: int | None = None,
    year: int | None = None,
    genre: str | None = None
) -> BookRecord:
    """
    Обновляет данные книги с указанным id.
    Возвращает обновлённую запись.
    Если книга не найдена, выбрасывает ValueError.
    Если передан новый author_id, проверяет его существование.
    """
    index = None
    for i, b in enumerate(Books):
        if b[0] == book_id:
            index = i
            break
    
    if index is None:
        raise ValueError(f"Книга с id={book_id} не найдена.")
    
    old = Books[index]
    
    
    if author_id is not None and not _author_exists(author_id):
        raise ValueError(f"Автор с id={author_id} не существует.")
    
   
    new_title = title.strip() if title is not None else old[1]
    new_author_id = author_id if author_id is not None else old[2]
    new_year = year if year is not None else old[3]
    new_genre = genre.strip() if genre is not None else old[4]
    
   
    if title is not None and not new_title:
        raise ValueError("Название книги не может быть пустым.")
    
    if year is not None and (year <= 0 or year > 2100):
        raise ValueError("Год должен быть положительным числом и не превышать 2100.")
    
    updated = (book_id, new_title, new_author_id, new_year, new_genre)
    Books[index] = updated
    return updated
    
def delete_book(
    book_id: int
    ) -> BookRecord:
    """
    Удаляет книгу с указанным id.
    Возвращает удалённую запись.
    Если книга не найдена, выбрасывает ValueError.
    """

    for i, b in enumerate(Books):
        if b[0] == book_id:
            deleted = Books.pop(i)
            return deleted
    raise ValueError(f"Книга с id={book_id} не найдена.")
    
