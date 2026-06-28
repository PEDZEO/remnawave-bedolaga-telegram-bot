from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


PAYMENT_TABLES = (
    'riopay_payments',
    'severpay_payments',
    'paypear_payments',
    'rollypay_payments',
    'overpay_payments',
    'aurapay_payments',
    'etoplatezhi_payments',
    'antilopay_payments',
    'jupiter_payments',
    'donut_payments',
    'lava_payments',
)


def load_migration_0050() -> ModuleType:
    path = (
        Path(__file__).resolve().parents[2]
        / 'migrations'
        / 'alembic'
        / 'versions'
        / '0050_add_extra_payment_providers.py'
    )
    spec = importlib.util.spec_from_file_location('migration_0050_add_extra_payment_providers', path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeInspector:
    def __init__(self, fake_op: FakeOp) -> None:
        self.fake_op = fake_op

    def get_table_names(self) -> list[str]:
        return sorted(self.fake_op.tables)

    def get_columns(self, table_name: str) -> list[dict[str, str]]:
        if table_name == 'kassa_ai_payments' and table_name in self.fake_op.tables:
            return [{'name': 'user_id'}]
        return []


class FakeOp:
    def __init__(self, existing_tables: set[str]) -> None:
        self.tables = set(existing_tables)
        self.created_tables: list[str] = []
        self.dropped_tables: list[str] = []
        self.altered_columns: list[tuple[str, str, dict[str, Any]]] = []

    def get_bind(self) -> object:
        return object()

    def create_table(self, table_name: str, *args: object, **kwargs: object) -> None:
        if table_name in self.tables:
            raise AssertionError(f'duplicate create_table call for {table_name}')
        self.tables.add(table_name)
        self.created_tables.append(table_name)

    def drop_table(self, table_name: str) -> None:
        if table_name not in self.tables:
            raise AssertionError(f'drop_table called for missing {table_name}')
        self.tables.remove(table_name)
        self.dropped_tables.append(table_name)

    def alter_column(self, table_name: str, column_name: str, **kwargs: Any) -> None:
        self.altered_columns.append((table_name, column_name, kwargs))


@pytest.fixture
def migration_0050(monkeypatch: pytest.MonkeyPatch) -> tuple[ModuleType, FakeOp]:
    module = load_migration_0050()
    fake_op = FakeOp(existing_tables={'kassa_ai_payments'})
    monkeypatch.setattr(module, 'op', fake_op)
    monkeypatch.setattr(module.sa, 'inspect', lambda _bind: FakeInspector(fake_op))
    return module, fake_op


def test_upgrade_skips_payment_tables_that_already_exist(
    migration_0050: tuple[ModuleType, FakeOp],
) -> None:
    module, fake_op = migration_0050
    fake_op.tables.update(PAYMENT_TABLES)

    module.upgrade()

    assert fake_op.created_tables == []
    assert fake_op.altered_columns[0][0:2] == ('kassa_ai_payments', 'user_id')


def test_upgrade_creates_only_missing_payment_tables(
    migration_0050: tuple[ModuleType, FakeOp],
) -> None:
    module, fake_op = migration_0050
    fake_op.tables.update({'riopay_payments', 'paypear_payments'})

    module.upgrade()

    assert fake_op.created_tables == [
        'severpay_payments',
        'rollypay_payments',
        'overpay_payments',
        'aurapay_payments',
        'etoplatezhi_payments',
        'antilopay_payments',
        'jupiter_payments',
        'donut_payments',
        'lava_payments',
    ]
