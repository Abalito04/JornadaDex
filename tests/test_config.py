import os
import unittest

os.environ.setdefault("SECRET_KEY", "test-secret-key")

from app.config import normalize_database_url


class ConfigTestCase(unittest.TestCase):
    def test_normalize_database_url_none_or_empty(self):
        self.assertIsNone(normalize_database_url(None))
        self.assertEqual(normalize_database_url(""), "")

    def test_normalize_database_url_postgres_prefix(self):
        url = "postgres://user:pass@host:5432/dbname"
        self.assertEqual(
            normalize_database_url(url),
            "postgresql://user:pass@host:5432/dbname"
        )

    def test_normalize_database_url_psycopg_prefix(self):
        url = "postgresql+psycopg://user:pass@host:5432/dbname"
        self.assertEqual(
            normalize_database_url(url),
            "postgresql+psycopg2://user:pass@host:5432/dbname"
        )

    def test_normalize_database_url_psycopg3_prefix(self):
        url = "postgresql+psycopg3://user:pass@host:5432/dbname"
        self.assertEqual(
            normalize_database_url(url),
            "postgresql+psycopg2://user:pass@host:5432/dbname"
        )

    def test_normalize_database_url_sqlite(self):
        url = "sqlite:///time_control.db"
        self.assertEqual(normalize_database_url(url), "sqlite:///time_control.db")
