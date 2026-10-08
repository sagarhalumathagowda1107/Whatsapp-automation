"""Initial schema for PSF, Recipients, Reports, and WhatsApp Message Logs

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-08 21:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # PSF Records
    op.create_table(
        'psf_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('value', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_psf_records_category'), 'psf_records', ['category'], unique=False)
    op.create_index(op.f('ix_psf_records_created_at'), 'psf_records', ['created_at'], unique=False)
    op.create_index(op.f('ix_psf_records_status'), 'psf_records', ['status'], unique=False)
    op.create_index(op.f('ix_psf_records_title'), 'psf_records', ['title'], unique=False)

    # Recipients
    op.create_table(
        'recipients',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('phone_number', sa.String(length=50), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recipients_active'), 'recipients', ['active'], unique=False)
    op.create_index(op.f('ix_recipients_phone_number'), 'recipients', ['phone_number'], unique=True)

    # Reports
    op.create_table(
        'reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('report_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('report_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_status'), 'reports', ['status'], unique=False)

    # WhatsApp Message Logs
    op.create_table(
        'whatsapp_message_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('report_id', sa.String(length=36), nullable=True),
        sa.Column('recipient_id', sa.String(length=36), nullable=True),
        sa.Column('whatsapp_message_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_code', sa.String(length=100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('request_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['recipient_id'], ['recipients.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_whatsapp_message_logs_recipient_id'), 'whatsapp_message_logs', ['recipient_id'], unique=False)
    op.create_index(op.f('ix_whatsapp_message_logs_report_id'), 'whatsapp_message_logs', ['report_id'], unique=False)
    op.create_index(op.f('ix_whatsapp_message_logs_status'), 'whatsapp_message_logs', ['status'], unique=False)
    op.create_index(op.f('ix_whatsapp_message_logs_whatsapp_message_id'), 'whatsapp_message_logs', ['whatsapp_message_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_whatsapp_message_logs_whatsapp_message_id'), table_name='whatsapp_message_logs')
    op.drop_index(op.f('ix_whatsapp_message_logs_status'), table_name='whatsapp_message_logs')
    op.drop_index(op.f('ix_whatsapp_message_logs_report_id'), table_name='whatsapp_message_logs')
    op.drop_index(op.f('ix_whatsapp_message_logs_recipient_id'), table_name='whatsapp_message_logs')
    op.drop_table('whatsapp_message_logs')

    op.drop_index(op.f('ix_reports_status'), table_name='reports')
    op.drop_table('reports')

    op.drop_index(op.f('ix_recipients_phone_number'), table_name='recipients')
    op.drop_index(op.f('ix_recipients_active'), table_name='recipients')
    op.drop_table('recipients')

    op.drop_index(op.f('ix_psf_records_title'), table_name='psf_records')
    op.drop_index(op.f('ix_psf_records_status'), table_name='psf_records')
    op.drop_index(op.f('ix_psf_records_created_at'), table_name='psf_records')
    op.drop_index(op.f('ix_psf_records_category'), table_name='psf_records')
    op.drop_table('psf_records')
