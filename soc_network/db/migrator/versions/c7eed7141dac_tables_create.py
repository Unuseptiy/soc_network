"""tables create

Revision ID: c7eed7141dac
Revises: 
Create Date: 2023-01-11 23:10:48.265339

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c7eed7141dac'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('dt_created', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('dt_updated', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('username', sa.TEXT(), nullable=False, unique=True),
    sa.Column('password', sa.TEXT(), nullable=False),
    sa.Column('email', sa.TEXT(), nullable=True, unique=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__user')),
    sa.UniqueConstraint('id', name=op.f('uq__user__id'))
    )
    op.create_index(op.f('ix__user__password'), 'user', ['password'], unique=False)
    op.create_index(op.f('ix__user__username'), 'user', ['username'], unique=True)
    op.create_table('post',
    sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('dt_created', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('dt_updated', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('body', sa.TEXT(), nullable=False),
    sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.ForeignKeyConstraint(['author_id'], ['user.id'], name=op.f('fk__post__author__user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk__post')),
    sa.UniqueConstraint('id', name=op.f('uq__post__id'))
    )
    op.create_table('post_action',
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('action', sa.TEXT(), nullable=False),
    sa.ForeignKeyConstraint(['post_id'], ['post.id'], name=op.f('fk__post_action__post_id__post')),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk__post_action__user_id__user')),
    sa.PrimaryKeyConstraint('user_id', 'post_id', 'action', name=op.f('pk__post_action'))
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('post_action')
    op.drop_table('post')
    op.drop_index(op.f('ix__user__username'), table_name='user')
    op.drop_index(op.f('ix__user__password'), table_name='user')
    op.drop_table('user')
    # ### end Alembic commands ###
