"""Тесты для модуля tui.py."""

import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

from src.db.tui import TUI


def _outputs(mock_print: MagicMock) -> str:
    """Собирает весь вывод print в одну строку для удобства проверок."""
    parts = []
    for call in mock_print.call_args_list:
        args, _ = call
        parts.append(" ".join(str(a) for a in args))
    return "\n".join(parts)


class TestTUIHelpers(unittest.TestCase):
    """Тесты вспомогательных методов TUI (без интерактива)."""

    def setUp(self):
        self.tui = TUI()

    def test_try_convert_int(self):
        cases = [("1", 1), ("-5", -5), ("0", 0), ("  42  ", 42)]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(self.tui._try_convert(raw), expected)

    def test_try_convert_float(self):
        cases = [("1.5", 1.5), ("-3.14", -3.14), ("0.0", 0.0)]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(self.tui._try_convert(raw), expected)

    def test_try_convert_string(self):
        cases = [("abc", "abc"), ("12abc", "12abc"), ("", "")]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(self.tui._try_convert(raw), expected)

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["abc", "10"])
    def test_read_int_retries_on_bad_input(self, _mock_input, mock_print):
        result = self.tui._read_int("prompt: ")
        self.assertEqual(result, 10)
        self.assertIn("введите целое число", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["-1", "0", "5"])
    def test_read_positive_int(self, _mock_input, mock_print):
        result = self.tui._read_positive_int("prompt: ")
        self.assertEqual(result, 5)
        self.assertIn("больше 0", _outputs(mock_print))


class TestTUIShowTables(unittest.TestCase):
    """Тесты show_tables и show_table_info."""

    def setUp(self):
        self.tui = TUI()

    @patch("builtins.print")
    def test_show_tables_empty(self, mock_print):
        self.tui.show_tables()
        self.assertIn("База данных пуста", _outputs(mock_print))

    @patch("builtins.print")
    def test_show_tables_with_data(self, mock_print):
        self.tui.db.create_table("users", ("id", "name"))
        self.tui.db.insert_record("users", {"id": 1, "name": "Alice"})
        self.tui.show_tables()
        out = _outputs(mock_print)
        self.assertIn("users", out)
        self.assertIn("Всего таблиц: 1", out)

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users"])
    def test_show_table_info_existing(self, _i, mock_print):
        self.tui.db.create_table("users", ("id", "name"))
        self.tui.db.insert_record("users", {"id": 1, "name": "Alice"})
        self.tui.show_table_info()
        out = _outputs(mock_print)
        self.assertIn("users", out)
        self.assertIn("Колонки", out)

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["nonexistent"])
    def test_show_table_info_missing(self, _i, mock_print):
        self.tui.show_table_info()
        self.assertIn("не существует", _outputs(mock_print))


class TestTUICreateTable(unittest.TestCase):
    def setUp(self):
        self.tui = TUI()

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "id, name, age"])
    def test_create_table_success(self, _i, mock_print):
        self.tui.create_table()
        self.assertTrue(self.tui.db.has_table("users"))
        self.assertIn("успешно создана", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["", "id, name"])
    def test_create_table_empty_name(self, _i, mock_print):
        self.tui.create_table()
        self.assertIn("пустым", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "name, age"])
    def test_create_table_no_id_first(self, _i, mock_print):
        self.tui.create_table()
        self.assertFalse(self.tui.db.has_table("users"))
        self.assertIn("id", _outputs(mock_print).lower())


class TestTUIInsertRecord(unittest.TestCase):
    def setUp(self):
        self.tui = TUI()
        self.tui.db.create_table("users", ("id", "name", "age"))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "1", "Alice", "25"])
    def test_insert_success(self, _i, mock_print):
        self.tui.insert_record()
        records = self.tui.db.select_records("users")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["name"], "Alice")
        self.assertEqual(records[0]["age"], 25)
        self.assertIn("успешно добавлена", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "abc", "1", "Bob", "30"])
    def test_insert_bad_id_retries(self, _i, mock_print):
        self.tui.insert_record()
        records = self.tui.db.select_records("users")
        self.assertEqual(len(records), 1)
        self.assertIn("целым числом", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["missing", "1", "Alice", "25"])
    def test_insert_missing_table(self, _i, mock_print):
        self.tui.insert_record()
        self.assertIn("не существует", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "1", "Bob", "30"])
    def test_insert_duplicate_id(self, _i, mock_print):
        self.tui.db.insert_record("users", {"id": 1, "name": "Alice", "age": 25})
        self.tui.insert_record()
        records = self.tui.db.select_records("users")
        self.assertEqual(len(records), 1)
        self.assertIn("уже существует", _outputs(mock_print))


class TestTUISelectRecords(unittest.TestCase):
    def setUp(self):
        self.tui = TUI()
        self.tui.db.create_table("users", ("id", "name", "age"))
        self.tui.db.insert_record("users", {"id": 1, "name": "Alice", "age": 25})
        self.tui.db.insert_record("users", {"id": 2, "name": "Bob", "age": 30})

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "n"])
    def test_select_no_filters(self, _i, mock_print):
        self.tui.select_records()
        out = _outputs(mock_print)
        self.assertIn("Найдено записей: 2", out)

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "y", "age", "25", ""])
    def test_select_with_filter(self, _i, mock_print):
        self.tui.select_records()
        out = _outputs(mock_print)
        self.assertIn("Найдено записей: 1", out)
        self.assertIn("Alice", out)

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "y", "missing_field", "x", ""])
    def test_select_invalid_filter_column(self, _i, mock_print):
        self.tui.select_records()
        self.assertIn("не определено", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["nope", "n"])
    def test_select_missing_table(self, _i, mock_print):
        self.tui.select_records()
        self.assertIn("не существует", _outputs(mock_print))


class TestTUIUpdateRecord(unittest.TestCase):
    def setUp(self):
        self.tui = TUI()
        self.tui.db.create_table("users", ("id", "name", "age"))
        self.tui.db.insert_record("users", {"id": 1, "name": "Alice", "age": 25})

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "1", "Alicia", ""])
    def test_update_success(self, _i, mock_print):
        self.tui.update_record()
        rec = self.tui.db.select_records("users", id=1)[0]
        self.assertEqual(rec["name"], "Alicia")
        self.assertIn("успешно обновлена", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "1", "", ""])
    def test_update_no_fields(self, _i, mock_print):
        self.tui.update_record()
        self.assertIn("Нет полей для обновления", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "999", "Alicia", ""])
    def test_update_record_not_found(self, _i, mock_print):
        self.tui.update_record()
        self.assertIn("не найдена", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["nope", "1", "Alicia", ""])
    def test_update_missing_table(self, _i, mock_print):
        self.tui.update_record()
        self.assertIn("не существует", _outputs(mock_print))


class TestTUIDeleteRecord(unittest.TestCase):
    def setUp(self):
        self.tui = TUI()
        self.tui.db.create_table("users", ("id", "name"))
        self.tui.db.insert_record("users", {"id": 1, "name": "Alice"})

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "1", "y"])
    def test_delete_success(self, _i, mock_print):
        self.tui.delete_record()
        self.assertEqual(len(self.tui.db.select_records("users")), 0)
        self.assertIn("успешно удалена", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "1", "n"])
    def test_delete_cancelled(self, _i, mock_print):
        self.tui.delete_record()
        self.assertEqual(len(self.tui.db.select_records("users")), 1)
        self.assertIn("отменено", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "999", "y"])
    def test_delete_not_found(self, _i, mock_print):
        self.tui.delete_record()
        self.assertIn("не найдена", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["nope", "1", "y"])
    def test_delete_missing_table(self, _i, mock_print):
        self.tui.delete_record()
        self.assertIn("не существует", _outputs(mock_print))


class TestTUISortRecords(unittest.TestCase):
    def setUp(self):
        self.tui = TUI()
        self.tui.db.create_table("users", ("id", "name", "age"))
        self.tui.db.insert_record("users", {"id": 3, "name": "C", "age": 35})
        self.tui.db.insert_record("users", {"id": 1, "name": "A", "age": 25})
        self.tui.db.insert_record("users", {"id": 2, "name": "B", "age": 30})

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "id", "asc"])
    def test_sort_asc(self, _i, mock_print):
        self.tui.sort_records()
        out = _outputs(mock_print)
        self.assertIn("Отсортировано записей: 3", out)
        pos_a = out.find("'name': 'A'")
        pos_b = out.find("'name': 'B'")
        pos_c = out.find("'name': 'C'")
        self.assertTrue(0 <= pos_a < pos_b < pos_c)

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "id", "desc"])
    def test_sort_desc(self, _i, mock_print):
        self.tui.sort_records()
        out = _outputs(mock_print)
        pos_a = out.find("'name': 'A'")
        pos_b = out.find("'name': 'B'")
        pos_c = out.find("'name': 'C'")
        self.assertTrue(pos_c < pos_b < pos_a)

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "nope", "asc"])
    def test_sort_invalid_column(self, _i, mock_print):
        self.tui.sort_records()
        self.assertIn("не определено", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["nope", "id", "asc"])
    def test_sort_missing_table(self, _i, mock_print):
        self.tui.sort_records()
        self.assertIn("не существует", _outputs(mock_print))


class TestTUIDropTable(unittest.TestCase):
    def setUp(self):
        self.tui = TUI()

    @patch("builtins.print")
    def test_drop_no_tables(self, mock_print):
        self.tui.drop_table()
        self.assertIn("Нет таблиц для удаления", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "y"])
    def test_drop_success(self, _i, mock_print):
        self.tui.db.create_table("users", ("id", "name"))
        self.tui.drop_table()
        self.assertFalse(self.tui.db.has_table("users"))
        self.assertIn("успешно удалена", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["users", "n"])
    def test_drop_cancelled(self, _i, mock_print):
        self.tui.db.create_table("users", ("id", "name"))
        self.tui.drop_table()
        self.assertTrue(self.tui.db.has_table("users"))
        self.assertIn("отменено", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["nope", "y"])
    def test_drop_missing_table(self, _i, mock_print):
        self.tui.db.create_table("users", ("id", "name"))
        self.tui.drop_table()
        self.assertIn("не существует", _outputs(mock_print))


class TestTUIRun(unittest.TestCase):
    """Тесты главного цикла run() — проверяем диспетчеризацию пунктов меню."""

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["0"])
    def test_run_exit_immediately(self, _i, mock_print):
        tui = TUI()
        tui.run()
        self.assertFalse(tui.running)
        self.assertIn("До свидания", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["1", "0"])
    def test_run_show_tables_then_exit(self, _i, mock_print):
        tui = TUI()
        tui.run()
        self.assertIn("СПИСОК ТАБЛИЦ", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["42", "0"])
    def test_run_invalid_choice(self, _i, mock_print):
        tui = TUI()
        tui.run()
        self.assertIn("Неверный выбор", _outputs(mock_print))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["3", "users", "id, name", "0"])
    def test_run_full_create_flow(self, _i, mock_print):
        tui = TUI()
        tui.run()
        self.assertTrue(tui.db.has_table("users"))


if __name__ == "__main__":
    unittest.main()