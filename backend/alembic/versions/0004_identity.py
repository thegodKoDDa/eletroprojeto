"""Identity and nullable ownership; legacy projects remain local until explicitly assigned."""
from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'


def upgrade():
    op.create_table('users', sa.Column('id', sa.String(36), primary_key=True),
                    sa.Column('username', sa.String(200), nullable=False, unique=True),
                    sa.Column('password_hash', sa.String(500), nullable=False),
                    sa.Column('active', sa.Boolean(), nullable=False))
    op.create_table('login_sessions', sa.Column('token_hash', sa.String(64), primary_key=True),
                    sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
                    sa.Column('csrf', sa.String(64), nullable=False),
                    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_login_sessions_user_id', 'login_sessions', ['user_id'])
    op.create_table('login_attempts', sa.Column('key', sa.String(64), primary_key=True),
                    sa.Column('failures', sa.Integer(), nullable=False),
                    sa.Column('window_start', sa.DateTime(timezone=True), nullable=False))
    with op.batch_alter_table('projects') as batch:
        batch.add_column(sa.Column('owner_id', sa.String(36), nullable=True))
        batch.create_foreign_key('fk_projects_owner_id', 'users', ['owner_id'], ['id'])
        batch.create_index('ix_projects_owner_id', ['owner_id'])


def downgrade():
    with op.batch_alter_table('projects') as batch:
        batch.drop_index('ix_projects_owner_id')
        batch.drop_constraint('fk_projects_owner_id', type_='foreignkey')
        batch.drop_column('owner_id')
    op.drop_table('login_attempts')
    op.drop_table('login_sessions')
    op.drop_table('users')
