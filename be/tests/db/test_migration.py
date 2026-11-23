"""Migration checks that need no server: run 0001 on SQLite, compare with the models, downgrade.

SQLite is only a structural stand-in here. The real run against Postgres is in tests/integration.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect

from app.db.models import Base

MIGRATION = Path(__file__).parents[2] / "alembic" / "versions" / "0001_initial_schema.py"


def _load() -> object:
    spec = importlib.util.spec_from_file_location("migration_0001", MIGRATION)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_matches_models_and_is_reversible() -> None:
    migration = _load()
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            migration.upgrade()  # type: ignore[attr-defined]
            inspector = inspect(connection)
            assert set(inspector.get_table_names()) == set(Base.metadata.tables)
            for name, table in Base.metadata.tables.items():
                migrated = {c["name"]: c for c in inspector.get_columns(name)}
                assert set(migrated) == {c.name for c in table.columns}, name
                for column in table.columns:
                    assert (
                        migrated[column.name]["nullable"] == column.nullable or column.primary_key
                    ), (
                        name,
                        column.name,
                    )
            migration.downgrade()  # type: ignore[attr-defined]
            assert inspect(connection).get_table_names() == []


def test_no_forbidden_columns() -> None:
    forbidden = {"calories", "kcal", "protein_g", "weight", "height", "bmi", "score"}
    names = {c.name for t in Base.metadata.tables.values() for c in t.columns}
    assert not forbidden & names
