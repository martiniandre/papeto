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

VERSIONS = Path(__file__).parents[2] / "alembic" / "versions"


def _load(path: Path) -> object:
    spec = importlib.util.spec_from_file_location(f"migration_{path.stem}", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _migrations() -> list[object]:
    """Every migration, oldest first (file names start with the sequence number)."""
    return [_load(path) for path in sorted(VERSIONS.glob("0*.py"))]


def test_migrations_match_models_and_are_reversible() -> None:
    migrations = _migrations()
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            for migration in migrations:
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
            for migration in reversed(migrations):
                migration.downgrade()  # type: ignore[attr-defined]
            assert inspect(connection).get_table_names() == []


def test_no_forbidden_columns() -> None:
    forbidden = {"calories", "kcal", "protein_g", "weight", "height", "bmi", "score"}
    names = {c.name for t in Base.metadata.tables.values() for c in t.columns}
    assert not forbidden & names
