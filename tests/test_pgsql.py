from unittest.mock import Mock

from src.db.pgsql import pgsql


def test_table_exists_uses_instance_table_name_by_default():
    database = pgsql.__new__(pgsql)
    database.table_name = "prices"
    database.inspector = Mock()
    database.inspector.has_table.return_value = True

    assert database.table_exists() is True
    database.inspector.has_table.assert_called_once_with("prices")


def test_table_exists_accepts_an_explicit_table_name():
    database = pgsql.__new__(pgsql)
    database.table_name = "prices"
    database.inspector = Mock()
    database.inspector.has_table.return_value = False

    assert database.table_exists("missing_table") is False
    database.inspector.has_table.assert_called_once_with("missing_table")
