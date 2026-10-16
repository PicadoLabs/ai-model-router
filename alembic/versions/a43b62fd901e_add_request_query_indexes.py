"""Add indexes for request history and routing decision queries."""

from alembic import op

revision = "a43b62fd901e"
down_revision = "e274a67cfc61"
branch_labels = None
depends_on = None

INDEXES = (
    ("ix_requests_timestamp", "requests", "timestamp"),
    ("ix_requests_task_type", "requests", "task_type"),
    ("ix_routing_decisions_request_id", "routing_decisions", "request_id"),
    ("ix_routing_decisions_timestamp", "routing_decisions", "timestamp"),
)


def upgrade():
    for name, table, column in INDEXES:
        op.create_index(name, table, [column], unique=False, if_not_exists=True)


def downgrade():
    for name, table, _ in reversed(INDEXES):
        op.drop_index(name, table_name=table)
