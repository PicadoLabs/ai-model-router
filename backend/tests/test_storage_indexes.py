import runpy
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, select

from app.storage.models import Base, RequestRecord, RoutingDecisionRecord


MIGRATION = runpy.run_path(str(Path(__file__).resolve().parents[2] / "alembic" / "versions" /
                               "a43b62fd901e_add_request_query_indexes.py"))
EXPECTED = {
    "requests": {"ix_requests_timestamp", "ix_requests_task_type", "ix_requests_workspace_id"},
    "routing_decisions": {"ix_routing_decisions_timestamp", "ix_routing_decisions_request_id"},
}


@pytest.fixture
def connection():
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        Base.metadata.create_all(conn)
        yield conn
    engine.dispose()


def assert_indexes(connection):
    for table, expected in EXPECTED.items():
        assert expected <= {index["name"] for index in inspect(connection).get_indexes(table)}


def test_fresh_tables_create_query_indexes(connection):
    assert_indexes(connection)


def test_migration_accepts_indexes_already_created_by_application_startup(connection):
    with Operations.context(MigrationContext.configure(connection)):
        MIGRATION["upgrade"]()
        MIGRATION["upgrade"]()
    assert_indexes(connection)


def test_migration_upgrades_existing_tables_and_downgrades_without_data_loss(connection):
    with Operations.context(MigrationContext.configure(connection)):
        MIGRATION["downgrade"]()
        connection.execute(RequestRecord.__table__.insert(), {
            "request_id": "fictional-request", "prompt": "test", "task_type": "CODING",
            "selected_model": "mock", "provider": "mock",
        })
        MIGRATION["upgrade"]()
        assert_indexes(connection)
        MIGRATION["downgrade"]()
    for name, table, _ in MIGRATION["INDEXES"]:
        assert name not in {index["name"] for index in inspect(connection).get_indexes(table)}
    assert connection.execute(select(RequestRecord.request_id)).scalar_one() == "fictional-request"
    assert "ix_requests_workspace_id" in {
        index["name"] for index in inspect(connection).get_indexes("requests")
    }


@pytest.mark.parametrize("query,index", [
    (select(RequestRecord).order_by(RequestRecord.timestamp.desc()).limit(10), "ix_requests_timestamp"),
    (select(RequestRecord).where(RequestRecord.workspace_id == "fictional"), "ix_requests_workspace_id"),
    (select(RequestRecord).where(RequestRecord.task_type == "CODING"), "ix_requests_task_type"),
    (select(RequestRecord).where(RequestRecord.request_id == "fictional"), "sqlite_autoindex_requests"),
    (select(RoutingDecisionRecord).where(RoutingDecisionRecord.request_id == "fictional"), "ix_routing_decisions_request_id"),
    (select(RoutingDecisionRecord).order_by(RoutingDecisionRecord.timestamp.desc()), "ix_routing_decisions_timestamp"),
])
def test_sqlite_query_plans_use_indexes(connection, query, index):
    sql = query.compile(dialect=connection.dialect, compile_kwargs={"literal_binds": True})
    plan = connection.exec_driver_sql("EXPLAIN QUERY PLAN " + str(sql)).all()
    assert any(index in row[-1] for row in plan), plan
