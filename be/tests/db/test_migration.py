"""Migration checks that need no server: run every revision on SQLite in order, compare the result
with the models, then downgrade all the way.

SQLite is only a structural stand-in here. The real run against Postgres is in tests/integration.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect

from app.db.models import Base

VERSIONS = Path(__file__).parents[2] / "alembic" / "versions"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"migration_{path.stem}", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ordered() -> list[ModuleType]:
    """Revisions from base to head, following `down_revision` links."""
    modules = [_load(path) for path in sorted(VERSIONS.glob("[0-9]*.py"))]
    by_down = {m.down_revision: m for m in modules}
    assert len(by_down) == len(modules), "migration history must be linear"
    chain: list[ModuleType] = []
    current = by_down.get(None)
    while current is not None:
        chain.append(current)
        current = by_down.get(current.revision)
    assert len(chain) == len(modules), "every migration must be reachable from the base"
    return chain


def test_migrations_match_models_and_are_reversible() -> None:
    chain = _ordered()
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            for migration in chain:
                migration.upgrade()
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
            for migration in reversed(chain):
                migration.downgrade()
            assert inspect(connection).get_table_names() == []


def test_no_forbidden_columns() -> None:
    forbidden = {"calories", "kcal", "protein_g", "weight", "height", "bmi", "score"}
    names = {c.name for t in Base.metadata.tables.values() for c in t.columns}
    assert not forbidden & names
