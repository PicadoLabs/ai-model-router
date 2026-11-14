"""Cascade request deletes to dependent records."""

from alembic import op
from sqlalchemy import inspect

revision = "f7ad29b54c16"
down_revision = "a43b62fd901e"
branch_labels = None
depends_on = None

_REQUEST_CHILD_TABLES = ("routing_decisions", "responses", "feedback", "experiment_runs")
_FK_NAMING = {"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"}


def _set_request_delete_rule(ondelete: str | None) -> None:
    inspector = inspect(op.get_bind())
    for table in _REQUEST_CHILD_TABLES:
        if not inspector.has_table(table):
            continue
        for foreign_key in inspector.get_foreign_keys(table):
            if foreign_key["constrained_columns"] != ["request_id"] or foreign_key["referred_table"] != "requests":
                continue
            current = foreign_key.get("options", {}).get("ondelete")
            if current == ondelete:
                break

            name = foreign_key["name"] or f"fk_{table}_request_id_requests"
            with op.batch_alter_table(table, naming_convention=_FK_NAMING) as batch:
                batch.drop_constraint(name, type_="foreignkey")
                batch.create_foreign_key(name, "requests", ["request_id"], ["request_id"], ondelete=ondelete)
            break


def upgrade() -> None:
    _set_request_delete_rule("CASCADE")


def downgrade() -> None:
    _set_request_delete_rule(None)
