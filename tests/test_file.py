"""Тесты модуля file.py (FileDatabase)."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from src.db.backend.errors import (
    ColumnNotFoundError,
    DuplicateIDError,
    InvalidDataError,
    InvalidStorageDataError,
    RecordNotFoundError,
    TableAlreadyExistsError,
    TableNotFoundError,
)
from src.db.backend.file import FileDatabase


class FileDatabaseTestCase(unittest.TestCase):
    """Базовый класс — создаёт временный каталог для каждого теста."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.directory = self._tmp.name
        self.db = FileDatabase(self.directory)

    def tearDown(self):
        self._tmp.cleanup()

    def _path(self, table_name: str) -> Path:
        return Path(self.directory) / f"{table_name}.json"

    def _read_file(self, table_name: str) -> dict:
        with self._path(table_name).open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write_raw(self, table_name: str, content: str) -> None:
        self._path(table_name).write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Инициализация
# ---------------------------------------------------------------------------

class TestFileDatabaseInit(FileDatabaseTestCase):
    """Инициализация и создание каталога."""

    def test_directory_is_created(self):
        new_dir = Path(self.directory) / "nested" / "subdir"
        self.assertFalse(new_dir.exists())
        FileDatabase(str(new_dir))
        self.assertTrue(new_dir.exists())
        self.assertTrue(new_dir.is_dir())

    def test_existing_directory_is_used(self):
        FileDatabase(self.directory)
        FileDatabase(self.directory)  # повторный вызов не падает

    def test_default_directory_is_data(self):
        cwd = os.getcwd()
        try:
            os.chdir(self.directory)
            FileDatabase()
            self.assertTrue((Path(self.directory) / "data").is_dir())
        finally:
            os.chdir(cwd)

    def test_empty_directory_has_no_tables(self):
        self.assertEqual(self.db.get_tables(), {})


# ---------------------------------------------------------------------------
# Таблицы
# ---------------------------------------------------------------------------

class TestFileDatabaseTables(FileDatabaseTestCase):
    """Создание, удаление, поиск таблиц."""

    def test_create_table_writes_file(self):
        self.db.create_table("users", ("id", "name"))
        self.assertTrue(self._path("users").exists())

    def test_create_table_file_content(self):
        self.db.create_table("users", ("id", "name"))
        self.assertEqual(
            self._read_file("users"),
            {"columns": ["id", "name"], "records": []},
        )

    def test_create_table_is_valid_utf8_json(self):
        """ensure_ascii=False — кириллица в данных не должна экранироваться."""
        self.db.create_table("users", ("id", "name"))
        self.db.insert_record("users", {"id": 1, "name": "Алиса"})
        raw = self._path("users").read_text(encoding="utf-8")
        self.assertIn("Алиса", raw)
        self.assertNotIn("\\u04", raw)

    def test_create_table_already_exists(self):
        self.db.create_table("users", ("id", "name"))
        with self.assertRaises(TableAlreadyExistsError):
            self.db.create_table("users", ("id", "name"))

    def test_create_table_invalid_columns(self):
        cases = [
            ((), "хотя бы одну"),
            (("name", "id"), "id"),
            (("id", "x", "x"), "уникальными"),
        ]
        for cols, fragment in cases:
            with self.subTest(columns=cols):
                with self.assertRaises(InvalidDataError) as ctx:
                    self.db.create_table("t", cols)
                self.assertIn(fragment, str(ctx.exception))

    def test_drop_table_deletes_file(self):
        self.db.create_table("users", ("id", "name"))
        self.assertTrue(self._path("users").exists())
        self.db.drop_table("users")
        self.assertFalse(self._path("users").exists())

    def test_drop_table_not_found(self):
        with self.assertRaises(TableNotFoundError):
            self.db.drop_table("ghost")

    def test_has_table(self):
        self.assertFalse(self.db.has_table("users"))
        self.db.create_table("users", ("id", "name"))
        self.assertTrue(self.db.has_table("users"))

    def test_has_table_after_drop(self):
        self.db.create_table("users", ("id",))
        self.db.drop_table("users")
        self.assertFalse(self.db.has_table("users"))

    def test_get_table_not_found(self):
        with self.assertRaises(TableNotFoundError):
            self.db.get_table("ghost")

    def test_get_table_returns_loaded_table(self):
        self.db.create_table("users", ("id", "name"))
        self.db.insert_record("users", {"id": 1, "name": "A"})
        table = self.db.get_table("users")
        self.assertEqual(table.get_columns(), ("id", "name"))
        self.assertEqual(len(table.get_records()), 1)

    def test_get_tables_lists_all(self):
        self.db.create_table("a", ("id",))
        self.db.create_table("b", ("id",))
        tables = self.db.get_tables()
        self.assertEqual(set(tables.keys()), {"a", "b"})

    def test_get_tables_empty(self):
        self.assertEqual(self.db.get_tables(), {})

    def test_list_table_names_ignores_non_json(self):
        """Файлы без .json в каталоге не должны попадать в список таблиц."""
        self.db.create_table("real", ("id",))
        (Path(self.directory) / "notes.txt").write_text("hello", encoding="utf-8")
        (Path(self.directory) / "README").write_text("hello", encoding="utf-8")
        self.assertEqual(set(self.db.get_tables().keys()), {"real"})


# ---------------------------------------------------------------------------
# Записи — проверка персистентности после каждой операции
# ---------------------------------------------------------------------------

class TestFileDatabaseRecords(FileDatabaseTestCase):
    """Операции над записями + проверка, что данные пишутся на диск."""

    def setUp(self):
        super().setUp()
        self.db.create_table("users", ("id", "name", "age"))

    def test_insert_persists_to_file(self):
        self.db.insert_record("users", {"id": 1, "name": "A", "age": 20})
        data = self._read_file("users")
        self.assertEqual(len(data["records"]), 1)
        self.assertEqual(data["records"][0], {"id": 1, "name": "A", "age": 20})

    def test_insert_multiple_persisted(self):
        self.db.insert_record("users", {"id": 1, "name": "A", "age": 20})
        self.db.insert_record("users", {"id": 2, "name": "B", "age": 30})
        self.assertEqual(len(self._read_file("users")["records"]), 2)

    def test_insert_duplicate_id(self):
        self.db.insert_record("users", {"id": 1, "name": "A", "age": 20})
        with self.assertRaises(DuplicateIDError):
            self.db.insert_record("users", {"id": 1, "name": "B", "age": 30})

    def test_insert_on_unknown_table(self):
        with self.assertRaises(TableNotFoundError):
            self.db.insert_record("ghost", {"id": 1})

    def test_insert_preserves_unicode(self):
        self.db.insert_record("users", {"id": 1, "name": "Алиса 🌸", "age": 25})
        data = self._read_file("users")
        self.assertEqual(data["records"][0]["name"], "Алиса 🌸")

    def test_select_returns_inserted_records(self):
        self.db.insert_record("users", {"id": 1, "name": "A", "age": 20})
        self.db.insert_record("users", {"id": 2, "name": "B", "age": 30})
        self.assertEqual(len(self.db.select_records("users")), 2)

    def test_select_with_filter(self):
        self.db.insert_record("users", {"id": 1, "name": "A", "age": 20})
        self.db.insert_record("users", {"id": 2, "name": "B", "age": 30})
        result = self.db.select_records("users", age=20)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1)

    def test_invalid_column_in_filter(self):
        with self.assertRaises(ColumnNotFoundError):
            self.db.select_records("users", unknown="x")

    def test_update_persists_to_file(self):
        self.db.insert_record("users", {"id": 1, "name": "A", "age": 20})
        self.db.update_record("users", 1, name="AA")
        self.assertEqual(self._read_file("users")["records"][0]["name"], "AA")

    def test_update_not_found(self):
        with self.assertRaises(RecordNotFoundError):
            self.db.update_record("users", 999, name="X")

    def test_delete_persists_to_file(self):
        self.db.insert_record("users", {"id": 1, "name": "A", "age": 20})
        self.db.insert_record("users", {"id": 2, "name": "B", "age": 30})
        self.db.delete_record("users", 1)
        data = self._read_file("users")
        self.assertEqual(len(data["records"]), 1)
        self.assertEqual(data["records"][0]["id"], 2)

    def test_delete_not_found(self):
        with self.assertRaises(RecordNotFoundError):
            self.db.delete_record("users", 999)

    def test_sort_records(self):
        for rec in [
            {"id": 3, "name": "C", "age": 35},
            {"id": 1, "name": "A", "age": 25},
            {"id": 2, "name": "B", "age": 30},
        ]:
            self.db.insert_record("users", rec)
        result = self.db.sort_records("users", "age")
        self.assertEqual([r["age"] for r in result], [25, 30, 35])

    def test_sort_does_not_mutate_file_order(self):
        """sort_records — чтение; файл переписываться не должен."""
        for rec in [
            {"id": 3, "name": "C", "age": 35},
            {"id": 1, "name": "A", "age": 25},
        ]:
            self.db.insert_record("users", rec)
        before = self._read_file("users")["records"]
        self.db.sort_records("users", "age")
        after = self._read_file("users")["records"]
        self.assertEqual(before, after)


# ---------------------------------------------------------------------------
# Персистентность между экземплярами
# ---------------------------------------------------------------------------

class TestFileDatabasePersistence(FileDatabaseTestCase):
    """Данные действительно переживают пересоздание объекта БД."""

    def test_data_survives_new_instance(self):
        self.db.create_table("users", ("id", "name"))
        self.db.insert_record("users", {"id": 1, "name": "Alice"})
        self.db.insert_record("users", {"id": 2, "name": "Bob"})

        db2 = FileDatabase(self.directory)
        self.assertTrue(db2.has_table("users"))
        records = db2.select_records("users")
        self.assertEqual(len(records), 2)
        self.assertEqual(sorted(r["name"] for r in records), ["Alice", "Bob"])

    def test_multiple_tables_persist(self):
        self.db.create_table("users", ("id", "name"))
        self.db.create_table("posts", ("id", "title"))
        self.db.insert_record("users", {"id": 1, "name": "A"})
        self.db.insert_record("posts", {"id": 1, "title": "Hello"})

        db2 = FileDatabase(self.directory)
        self.assertEqual(set(db2.get_tables().keys()), {"users", "posts"})
        self.assertEqual(db2.select_records("users")[0]["name"], "A")
        self.assertEqual(db2.select_records("posts")[0]["title"], "Hello")

    def test_drop_then_recreate_instance(self):
        self.db.create_table("users", ("id", "name"))
        self.db.insert_record("users", {"id": 1, "name": "A"})
        self.db.drop_table("users")

        db2 = FileDatabase(self.directory)
        self.assertFalse(db2.has_table("users"))

    def test_update_visible_in_new_instance(self):
        self.db.create_table("users", ("id", "name"))
        self.db.insert_record("users", {"id": 1, "name": "A"})
        self.db.update_record("users", 1, name="Z")

        db2 = FileDatabase(self.directory)
        self.assertEqual(db2.select_records("users")[0]["name"], "Z")


# ---------------------------------------------------------------------------
# Повреждённые файлы хранилища
# ---------------------------------------------------------------------------

class TestFileDatabaseCorruptedFiles(FileDatabaseTestCase):
    """Обработка повреждённых файлов хранилища."""

    def test_invalid_json_raises(self):
        self._write_raw("broken", "{ this is not json")
        with self.assertRaises(InvalidStorageDataError):
            self.db.get_table("broken")

    def test_empty_file_raises(self):
        self._write_raw("broken", "")
        with self.assertRaises(InvalidStorageDataError):
            self.db.get_table("broken")

    def test_missing_columns_field(self):
        self._write_raw("broken", json.dumps({"records": []}))
        with self.assertRaises(InvalidStorageDataError):
            self.db.get_table("broken")

    def test_missing_records_field(self):
        self._write_raw("broken", json.dumps({"columns": ["id"]}))
        with self.assertRaises(InvalidStorageDataError):
            self.db.get_table("broken")

    def test_columns_not_a_list(self):
        self._write_raw("broken", json.dumps({"columns": "id", "records": []}))
        with self.assertRaises(InvalidStorageDataError):
            self.db.get_table("broken")

    def test_records_not_a_list(self):
        self._write_raw("broken", json.dumps({"columns": ["id"], "records": {}}))
        with self.assertRaises(InvalidStorageDataError):
            self.db.get_table("broken")

    def test_record_not_a_dict(self):
        self._write_raw(
            "broken",
            json.dumps({"columns": ["id"], "records": [[1, 2]]}),
        )
        with self.assertRaises(InvalidStorageDataError):
            self.db.get_table("broken")

    def test_root_not_a_dict(self):
        self._write_raw("broken", json.dumps([1, 2, 3]))
        with self.assertRaises(InvalidStorageDataError):
            self.db.get_table("broken")

    def test_root_is_null(self):
        self._write_raw("broken", "null")
        with self.assertRaises(InvalidStorageDataError):
            self.db.get_table("broken")

    def test_column_not_a_string(self):
        self._write_raw(
            "broken",
            json.dumps({"columns": ["id", 42], "records": []}),
        )
        with self.assertRaises(InvalidStorageDataError):
            self.db.get_table("broken")

    def test_column_is_none(self):
        self._write_raw(
            "broken",
            json.dumps({"columns": ["id", None], "records": []}),
        )
        with self.assertRaises(InvalidStorageDataError):
            self.db.get_table("broken")

    def test_column_is_empty_string(self):
        self._write_raw(
            "broken",
            json.dumps({"columns": ["id", ""], "records": []}),
        )
        with self.assertRaises(InvalidStorageDataError):
            self.db.get_table("broken")

    def test_column_is_nested_list(self):
        self._write_raw(
            "broken",
            json.dumps({"columns": ["id", ["x"]], "records": []}),
        )
        with self.assertRaises(InvalidStorageDataError):
            self.db.get_table("broken")

    def test_corrupted_file_does_not_break_listing(self):
        """Битый файл лежит в каталоге — get_tables не должен падать.

        get_tables пропускает битые файлы и возвращает только валидные таблицы.
        """
        self.db.create_table("good", ("id",))
        self._write_raw("broken", "{ not json")
        tables = self.db.get_tables()
        self.assertIn("good", tables)
        self.assertNotIn("broken", tables)

    def test_listing_skips_broken_but_keeps_valid(self):
        """Несколько валидных таблиц остаются доступны рядом с битой."""
        self.db.create_table("users", ("id", "name"))
        self.db.create_table("posts", ("id", "title"))
        self.db.insert_record("users", {"id": 1, "name": "A"})
        self._write_raw("broken", "{ not json")
        tables = self.db.get_tables()
        self.assertIn("users", tables)
        self.assertIn("posts", tables)
        self.assertNotIn("broken", tables)


# ---------------------------------------------------------------------------
# Path traversal — валидация имени таблицы
# ---------------------------------------------------------------------------

class TestFileDatabasePathTraversal(FileDatabaseTestCase):
    """Имя таблицы не должно позволять выйти за пределы каталога."""

    def test_dotdot_in_name_rejected(self):
        with self.assertRaises(InvalidDataError):
            self.db.create_table("../evil", ("id",))

    def test_slash_in_name_rejected(self):
        with self.assertRaises(InvalidDataError):
            self.db.create_table("a/b", ("id",))

    def test_absolute_path_rejected(self):
        with self.assertRaises(InvalidDataError):
            self.db.create_table("/tmp/evil", ("id",))

    def test_dot_only_rejected(self):
        with self.assertRaises(InvalidDataError):
            self.db.create_table(".", ("id",))

    def test_empty_name_rejected(self):
        with self.assertRaises(InvalidDataError):
            self.db.create_table("", ("id",))

    def test_cyrillic_name_rejected(self):
        with self.assertRaises(InvalidDataError):
            self.db.create_table("пользователи", ("id",))

    def test_name_too_long_rejected(self):
        with self.assertRaises(InvalidDataError):
            self.db.create_table("a" * 65, ("id",))

    def test_valid_names_accepted(self):
        """Граничные случаи допустимых имён."""
        valid = ["a", "A", "users", "my-table", "my_table", "t1", "a" * 64]
        for name in valid:
            with self.subTest(name=name):
                self.db.create_table(name, ("id",))
                self.assertTrue(self.db.has_table(name))
                self.db.drop_table(name)


if __name__ == "__main__":
    unittest.main()