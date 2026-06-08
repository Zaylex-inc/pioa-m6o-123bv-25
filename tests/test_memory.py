"""Тесты модулей memory.py и errors.py."""

import unittest

from src.db.backend.errors import (
    ColumnNotFoundError,
    DatabaseError,
    DuplicateIDError,
    InvalidDataError,
    RecordNotFoundError,
    TableNotFoundError,
)
from src.db.backend.memory import Database, Table


class TestTableInit(unittest.TestCase):
    """Инициализация таблицы и валидация колонок."""

    def test_table_allocation(self):
        table = Table("users", ("id", "name"))
        self.assertIsInstance(table, Table)
        self.assertEqual(table.get_name(), "users")
        self.assertEqual(table.get_columns(), ("id", "name"))
        self.assertEqual(table.get_record_count(), 0)

    def test_empty_columns(self):
        with self.assertRaises(InvalidDataError) as ctx:
            Table("t", ())
        self.assertIn("хотя бы одну колонку", str(ctx.exception))

    def test_id_must_be_first(self):
        cases = [
            ("name", "id"),
            ("age", "id", "name"),
            ("name", "age"),
        ]
        for cols in cases:
            with self.subTest(columns=cols):
                with self.assertRaises(InvalidDataError) as ctx:
                    Table("t", cols)
                self.assertIn("id", str(ctx.exception))

    def test_duplicate_columns(self):
        with self.assertRaises(InvalidDataError) as ctx:
            Table("t", ("id", "name", "name"))
        self.assertIn("уникальными", str(ctx.exception))


class TestTableInsert(unittest.TestCase):
    """Вставка записей в таблицу."""

    def setUp(self):
        self.table = Table("users", ("id", "name", "age", "email"))

    def test_insert_success(self):
        rec = {"id": 1, "name": "Alice", "age": 25, "email": "a@x"}
        result = self.table.insert_record(rec)
        self.assertEqual(result, rec)
        self.assertEqual(self.table.get_record_count(), 1)

    def test_insert_multiple(self):
        records = [
            {"id": 1, "name": "A", "age": 20, "email": "a@x"},
            {"id": 2, "name": "B", "age": 21, "email": "b@x"},
            {"id": 3, "name": "C", "age": 22, "email": "c@x"},
        ]
        for rec in records:
            with self.subTest(record=rec):
                self.table.insert_record(rec)
        self.assertEqual(self.table.get_record_count(), 3)

    def test_insert_missing_id_field(self):
        with self.assertRaises(InvalidDataError) as ctx:
            self.table.insert_record({"name": "A", "age": 20, "email": "a@x"})
        self.assertIn("id", str(ctx.exception))

    def test_insert_missing_other_field(self):
        with self.assertRaises(InvalidDataError) as ctx:
            self.table.insert_record({"id": 1, "name": "A", "age": 20})
        self.assertIn("email", str(ctx.exception))

    def test_insert_invalid_id_type(self):
        cases = ["1", 1.5, None, [1], {"x": 1}, True, False]
        for bad_id in cases:
            with self.subTest(id=bad_id):
                rec = {"id": bad_id, "name": "A", "age": 20, "email": "a@x"}
                with self.assertRaises(InvalidDataError):
                    self.table.insert_record(rec)

    def test_insert_extra_column(self):
        rec = {"id": 1, "name": "A", "age": 20, "email": "a@x", "extra": 1}
        with self.assertRaises(ColumnNotFoundError) as ctx:
            self.table.insert_record(rec)
        self.assertIn("extra", str(ctx.exception))

    def test_insert_duplicate_id(self):
        self.table.insert_record({"id": 1, "name": "A", "age": 20, "email": "a@x"})
        with self.assertRaises(DuplicateIDError) as ctx:
            self.table.insert_record(
                {"id": 1, "name": "B", "age": 21, "email": "b@x"}
            )
        self.assertIn("id=1", str(ctx.exception))

    def test_insert_returns_copy(self):
        rec = {"id": 1, "name": "A", "age": 20, "email": "a@x"}
        returned = self.table.insert_record(rec)
        returned["name"] = "MUTATED"
        stored = self.table.select_records(id=1)[0]
        self.assertEqual(stored["name"], "A")


class TestTableSelect(unittest.TestCase):
    """Выборка записей."""

    def setUp(self):
        self.table = Table("users", ("id", "name", "age", "sex"))
        self.data = [
            {"id": 1, "name": "Alice", "age": 25, "sex": "F"},
            {"id": 2, "name": "Bob", "age": 30, "sex": "M"},
            {"id": 3, "name": "Carol", "age": 25, "sex": "F"},
            {"id": 4, "name": "Dan", "age": 40, "sex": "M"},
        ]
        for rec in self.data:
            self.table.insert_record(rec)

    def test_select_no_filters(self):
        result = self.table.select_records()
        self.assertEqual(len(result), 4)

    def test_select_with_filters(self):
        cases = [
            ({"id": 1}, [self.data[0]]),
            ({"name": "Bob"}, [self.data[1]]),
            ({"age": 25}, [self.data[0], self.data[2]]),
            ({"sex": "M"}, [self.data[1], self.data[3]]),
            ({"age": 25, "sex": "F"}, [self.data[0], self.data[2]]),
            ({"age": 100}, []),
        ]
        for filters, expected in cases:
            with self.subTest(filters=filters):
                result = self.table.select_records(**filters)
                self.assertEqual(result, expected)

    def test_select_invalid_column(self):
        with self.assertRaises(ColumnNotFoundError) as ctx:
            self.table.select_records(unknown="x")
        self.assertIn("unknown", str(ctx.exception))

    def test_select_returns_copy(self):
        result = self.table.select_records()
        result[0]["name"] = "MUTATED"
        again = self.table.select_records(id=1)
        self.assertEqual(again[0]["name"], "Alice")

    def test_get_records_returns_copy(self):
        records = self.table.get_records()
        records.clear()
        self.assertEqual(self.table.get_record_count(), 4)


class TestTableUpdate(unittest.TestCase):
    """Обновление записей."""

    def setUp(self):
        self.table = Table("users", ("id", "name", "age", "email"))
        self.table.insert_record(
            {"id": 1, "name": "Alice", "age": 25, "email": "a@x"}
        )
        self.table.insert_record(
            {"id": 2, "name": "Bob", "age": 30, "email": "b@x"}
        )

    def test_update_success(self):
        result = self.table.update_record(1, name="Alicia", age=26)
        self.assertEqual(result["name"], "Alicia")
        self.assertEqual(result["age"], 26)
        self.assertEqual(result["email"], "a@x")

    def test_update_partial(self):
        result = self.table.update_record(1, name="Alicia")
        self.assertEqual(result["name"], "Alicia")
        self.assertEqual(result["age"], 25)

    def test_update_empty_updates(self):
        result = self.table.update_record(1)
        self.assertEqual(result["name"], "Alice")

    def test_update_invalid_id_type(self):
        for bad in ["1", 1.5, None, True]:
            with self.subTest(id=bad):
                with self.assertRaises(InvalidDataError):
                    self.table.update_record(bad, name="X")

    def test_update_not_found(self):
        with self.assertRaises(RecordNotFoundError) as ctx:
            self.table.update_record(999, name="X")
        self.assertIn("id=999", str(ctx.exception))

    def test_update_invalid_column_fail_fast(self):
        """При невалидной колонке запись не должна меняться."""
        with self.assertRaises(ColumnNotFoundError):
            self.table.update_record(1, name="Alicia", unknown="X")
        # name НЕ должно было измениться
        rec = self.table.select_records(id=1)[0]
        self.assertEqual(rec["name"], "Alice")


class TestTableDelete(unittest.TestCase):
    """Удаление записей."""

    def setUp(self):
        self.table = Table("users", ("id", "name"))
        self.table.insert_record({"id": 1, "name": "A"})
        self.table.insert_record({"id": 2, "name": "B"})

    def test_delete_success(self):
        deleted = self.table.delete_record(1)
        self.assertEqual(deleted["name"], "A")
        self.assertEqual(self.table.get_record_count(), 1)

    def test_delete_invalid_id_type(self):
        for bad in ["1", 1.5, None, True]:
            with self.subTest(id=bad):
                with self.assertRaises(InvalidDataError):
                    self.table.delete_record(bad)

    def test_delete_not_found(self):
        with self.assertRaises(RecordNotFoundError) as ctx:
            self.table.delete_record(999)
        self.assertIn("id=999", str(ctx.exception))


class TestTableSort(unittest.TestCase):
    """Сортировка записей."""

    def setUp(self):
        self.table = Table("users", ("id", "name", "age"))
        for rec in [
            {"id": 3, "name": "Charlie", "age": 35},
            {"id": 1, "name": "Alice", "age": 25},
            {"id": 2, "name": "Bob", "age": 30},
        ]:
            self.table.insert_record(rec)

    def test_sort_ascending_int(self):
        result = self.table.sort_records("id")
        self.assertEqual([r["id"] for r in result], [1, 2, 3])

    def test_sort_descending_int(self):
        result = self.table.sort_records("id", descending=True)
        self.assertEqual([r["id"] for r in result], [3, 2, 1])

    def test_sort_by_string(self):
        result = self.table.sort_records("name")
        self.assertEqual(
            [r["name"] for r in result], ["Alice", "Bob", "Charlie"]
        )

    def test_sort_by_string_descending(self):
        result = self.table.sort_records("name", descending=True)
        self.assertEqual(
            [r["name"] for r in result], ["Charlie", "Bob", "Alice"]
        )

    def test_sort_does_not_mutate(self):
        before = self.table.select_records()
        self.table.sort_records("id")
        after = self.table.select_records()
        self.assertEqual(before, after)

    def test_sort_invalid_column(self):
        with self.assertRaises(ColumnNotFoundError):
            self.table.sort_records("unknown")

    def test_sort_with_none_values(self):
        t = Table("t", ("id", "value"))
        t.insert_record({"id": 1, "value": 10})
        t.insert_record({"id": 2, "value": None})
        t.insert_record({"id": 3, "value": 5})
        result = t.sort_records("value")
        # None должен оказаться в конце.
        self.assertIsNone(result[-1]["value"])
        self.assertEqual([r["value"] for r in result[:-1]], [5, 10])

    def test_sort_mixed_types_raises(self):
        t = Table("t", ("id", "value"))
        t.insert_record({"id": 1, "value": 10})
        t.insert_record({"id": 2, "value": "ten"})
        with self.assertRaises(InvalidDataError):
            t.sort_records("value")


class TestDatabase(unittest.TestCase):
    """Тесты класса Database."""

    def setUp(self):
        self.db = Database()

    def test_create_table(self):
        self.db.create_table("users", ("id", "name"))
        self.assertTrue(self.db.has_table("users"))

    def test_create_table_already_exists(self):
        self.db.create_table("users", ("id", "name"))
        with self.assertRaises(DatabaseError) as ctx:
            self.db.create_table("users", ("id", "name"))
        self.assertIn("уже существует", str(ctx.exception))

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

    def test_drop_table(self):
        self.db.create_table("users", ("id", "name"))
        self.db.drop_table("users")
        self.assertFalse(self.db.has_table("users"))

    def test_drop_table_not_found(self):
        with self.assertRaises(TableNotFoundError):
            self.db.drop_table("ghost")

    def test_get_table_not_found(self):
        with self.assertRaises(TableNotFoundError):
            self.db.get_table("ghost")

    def test_get_tables_returns_copy(self):
        self.db.create_table("a", ("id",))
        snapshot = self.db.get_tables()
        snapshot.clear()
        self.assertTrue(self.db.has_table("a"))

    def test_has_table(self):
        self.assertFalse(self.db.has_table("x"))
        self.db.create_table("x", ("id",))
        self.assertTrue(self.db.has_table("x"))


class TestDatabaseDelegation(unittest.TestCase):
    """Database корректно проксирует операции в Table."""

    def setUp(self):
        self.db = Database()
        self.db.create_table("users", ("id", "name", "age"))
        self.db.insert_record("users", {"id": 1, "name": "A", "age": 20})
        self.db.insert_record("users", {"id": 2, "name": "B", "age": 30})

    def test_insert_on_unknown_table(self):
        with self.assertRaises(TableNotFoundError):
            self.db.insert_record("ghost", {"id": 1})

    def test_select_all(self):
        result = self.db.select_records("users")
        self.assertEqual(len(result), 2)

    def test_select_with_filter(self):
        result = self.db.select_records("users", name="A")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1)

    def test_select_on_unknown_table(self):
        with self.assertRaises(TableNotFoundError):
            self.db.select_records("ghost")

    def test_update(self):
        result = self.db.update_record("users", 1, name="AA")
        self.assertEqual(result["name"], "AA")

    def test_update_on_unknown_table(self):
        with self.assertRaises(TableNotFoundError):
            self.db.update_record("ghost", 1, name="X")

    def test_delete(self):
        self.db.delete_record("users", 1)
        self.assertEqual(len(self.db.select_records("users")), 1)

    def test_delete_on_unknown_table(self):
        with self.assertRaises(TableNotFoundError):
            self.db.delete_record("ghost", 1)

    def test_sort(self):
        result = self.db.sort_records("users", "age", descending=True)
        self.assertEqual([r["age"] for r in result], [30, 20])

    def test_sort_on_unknown_table(self):
        with self.assertRaises(TableNotFoundError):
            self.db.sort_records("ghost", "id")

    def test_multiple_tables_isolated(self):
        self.db.create_table("posts", ("id", "title"))
        self.db.insert_record("posts", {"id": 1, "title": "Hello"})
        self.assertEqual(len(self.db.select_records("users")), 2)
        self.assertEqual(len(self.db.select_records("posts")), 1)


if __name__ == "__main__":
    unittest.main()