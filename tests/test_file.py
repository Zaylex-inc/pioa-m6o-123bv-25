"""Тесты модуля file.py (FileDatabase)."""

import json
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


class TestFileDatabaseInit(FileDatabaseTestCase):
    """Инициализация и создание каталога."""

    def test_directory_is_created(self):
        new_dir = Path(self.directory) / "nested" / "subdir"
        self.assertFalse(new_dir.exists())
        FileDatabase(str(new_dir))
        self.assertTrue(new_dir.exists())

    def test_existing_directory_is_used(self):
        FileDatabase(self.directory)
        FileDatabase(self.directory)  # повторный вызов не падает


class TestFileDatabaseTables(FileDatabaseTestCase):
    """Создание, удаление и проверка таблиц."""

    def test_create_table_writes_file(self):
        self.db.create_table("users", ("id", "name"))
        path = Path(self.directory) / "users.json"
        self.assertTrue(path.exists())

    def test_create_table_file_content(self):
        self.db.create_table("users", ("id", "name"))
        path = Path(self.directory) / "users.json"
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data, {"columns": ["id", "name"], "records": []})

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
        path = Path(self.directory) / "users.json"
        self.assertTrue(path.exists())
        self.db.drop_table("users")
        self.assertFalse(path.exists())

    def test_drop_table_not_found(self):
        with self.assertRaises(TableNotFoundError):
            self.db.drop_table("ghost")

    def test_has_table(self):
        self.assertFalse(self.db.has_table("users"))
        self.db.create_table("users", ("id", "name"))
        self.assertTrue(self.db.has_table("users"))

    def test_get_table_not_found(self):
        with self.assertRaises(TableNotFoundError):
            self.db.get_table("ghost")

    def test_get_tables_lists_all(self):
        self.db.create_table("a", ("id",))
        self.db.create_table("b", ("id",))
        tables = self.db.get_tables()
        self.assertEqual(set(tables.keys()), {"a", "b"})


class TestFileDatabaseRecords(FileDatabaseTestCase):
    """Операции над записями + проверка, что данные пишутся на диск."""

    def setUp(self):
        super().setUp()
        self.db.create_table("users", ("id", "name", "age"))

    def _read_file(self, table_name: str) -> dict:
        path = Path(self.directory) / f"{table_name}.json"
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def test_insert_persists_to_file(self):
        self.db.insert_record("users", {"id": 1, "name": "A", "age": 20})
        data = self._read_file("users")
        self.assertEqual(len(data["records"]), 1)
        self.assertEqual(data["records"][0], {"id": 1, "name": "A", "age": 20})

    def test_insert_multiple_persisted(self):
        self.db.insert_record("users", {"id": 1, "name": "A", "age": 20})
        self.db.insert_record("users", {"id": 2, "name": "B", "age": 30})
        data = self._read_file("users")
        self.assertEqual(len(data["records"]), 2)

    def test_insert_duplicate_id(self):
        self.db.insert_record("users", {"id": 1, "name": "A", "age": 20})
        with self.assertRaises(DuplicateIDError):
            self.db.insert_record("users", {"id": 1, "name": "B", "age": 30})

    def test_insert_on_unknown_table(self):
        with self.assertRaises(TableNotFoundError):
            self.db.insert_record("ghost", {"id": 1})

    def test_select_returns_inserted_records(self):
        self.db.insert_record("users", {"id": 1, "name": "A", "age": 20})
        self.db.insert_record("users", {"id": 2, "name": "B", "age": 30})
        result = self.db.select_records("users")
        self.assertEqual(len(result), 2)

    def test_select_with_filter(self):
        self.db.insert_record("users", {"id": 1, "name": "A", "age": 20})
        self.db.insert_record("users", {"id": 2, "name": "B", "age": 30})
        result = self.db.select_records("users", age=20)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1)

    def test_update_persists_to_file(self):
        self.db.insert_record("users", {"id": 1, "name": "A", "age": 20})
        self.db.update_record("users", 1, name="AA")
        data = self._read_file("users")
        self.assertEqual(data["records"][0]["name"], "AA")

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

    def test_invalid_column_in_filter(self):
        with self.assertRaises(ColumnNotFoundError):
            self.db.select_records("users", unknown="x")


class TestFileDatabasePersistence(FileDatabaseTestCase):
    """Данные действительно переживают пересоздание объекта БД."""

    def test_data_survives_new_instance(self):
        self.db.create_table("users", ("id", "name"))
        self.db.insert_record("users", {"id": 1, "name": "Alice"})
        self.db.insert_record("users", {"id": 2, "name": "Bob"})

        # Создаём новый экземпляр на том же каталоге.
        db2 = FileDatabase(self.directory)
        self.assertTrue(db2.has_table("users"))
        records = db2.select_records("users")
        self.assertEqual(len(records), 2)
        self.assertEqual(
            sorted(r["name"] for r in records), ["Alice", "Bob"]
        )

    def test_multiple_tables_persist(self):
        self.db.create_table("users", ("id", "name"))
        self.db.create_table("posts", ("id", "title"))
        self.db.insert_record("users", {"id": 1, "name": "A"})
        self.db.insert_record("posts", {"id": 1, "title": "Hello"})

        db2 = FileDatabase(self.directory)
        self.assertEqual(set(db2.get_tables().keys()), {"users", "posts"})

    def test_drop_then_recreate_instance(self):
        self.db.create_table("users", ("id", "name"))
        self.db.insert_record("users", {"id": 1, "name": "A"})
        self.db.drop_table("users")

        db2 = FileDatabase(self.directory)
        self.assertFalse(db2.has_table("users"))


class TestFileDatabaseCorruptedFiles(FileDatabaseTestCase):
    """Обработка повреждённых файлов хранилища."""

    def _write_raw(self, table_name: str, content: str) -> None:
        path = Path(self.directory) / f"{table_name}.json"
        path.write_text(content, encoding="utf-8")

    def test_invalid_json_raises(self):
        self._write_raw("broken", "{ this is not json")
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
        self._write_raw(
            "broken", json.dumps({"columns": "id", "records": []})
        )
        with self.assertRaises(InvalidStorageDataError):
            self.db.get_table("broken")

    def test_records_not_a_list(self):
        self._write_raw(
            "broken", json.dumps({"columns": ["id"], "records": {}})
        )
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


if __name__ == "__main__":
    unittest.main()
