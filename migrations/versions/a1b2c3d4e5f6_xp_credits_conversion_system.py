"""XP Credits Conversion System

Revision ID: a1b2c3d4e5f6
Revises: f5a9c7b8d123
Create Date: 2026-01-26

Adiciona sistema de conversao de XP para creditos:
- ConversionRule: Regras de conversao (admin)
- CreditWallet: Carteiras de creditos com expiracao
- XPConversion: Historico de conversoes
- XPLedger: Controle granular de XP
- Campos de cache no User
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f5a9c7b8d123'
branch_labels = None
depends_on = None


def upgrade():
    # Tabela: conversion_rules
    op.create_table('conversion_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('xp_required', sa.Integer(), nullable=False),
        sa.Column('credits_granted', sa.Integer(), nullable=False),
        sa.Column('credit_validity_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('is_automatic', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('max_uses_per_user', sa.Integer(), nullable=True),
        sa.Column('cooldown_days', sa.Integer(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Tabela: credit_wallets
    op.create_table('credit_wallets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('credits_initial', sa.Integer(), nullable=False),
        sa.Column('credits_remaining', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.Enum('PURCHASE', 'CONVERSION', 'BONUS', 'REFUND', name='creditsourcetype'), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_expired', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # Index FIFO para credit_wallets
    op.create_index('ix_credit_wallet_fifo', 'credit_wallets', ['user_id', 'is_expired', 'expires_at', 'created_at'], unique=False)

    # Tabela: xp_ledger
    op.create_table('xp_ledger',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('xp_amount', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.Enum('CLASS', 'ACHIEVEMENT', 'BONUS', 'STREAK', 'REFERRAL', 'ADMIN', name='xpsourcetype'), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('earned_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('converted_amount', sa.Integer(), nullable=True, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # Index para xp_ledger
    op.create_index('ix_xp_ledger_user_available', 'xp_ledger', ['user_id', 'expires_at', 'converted_amount'], unique=False)

    # Tabela: xp_conversions
    op.create_table('xp_conversions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('xp_spent', sa.Integer(), nullable=False),
        sa.Column('credits_granted', sa.Integer(), nullable=False),
        sa.Column('wallet_id', sa.Integer(), nullable=True),
        sa.Column('is_automatic', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('converted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['rule_id'], ['conversion_rules.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['wallet_id'], ['credit_wallets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # Index para xp_conversions
    op.create_index('ix_xp_conversion_user_date', 'xp_conversions', ['user_id', 'converted_at'], unique=False)

    # Adiciona campos de cache ao User
    op.add_column('users', sa.Column('xp_available', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('users', sa.Column('credits_balance', sa.Integer(), nullable=True, server_default='0'))


def downgrade():
    # Remove campos de cache do User
    op.drop_column('users', 'credits_balance')
    op.drop_column('users', 'xp_available')

    # Remove tabelas na ordem correta (dependencias)
    op.drop_index('ix_xp_conversion_user_date', table_name='xp_conversions')
    op.drop_table('xp_conversions')

    op.drop_index('ix_xp_ledger_user_available', table_name='xp_ledger')
    op.drop_table('xp_ledger')

    op.drop_index('ix_credit_wallet_fifo', table_name='credit_wallets')
    op.drop_table('credit_wallets')

    op.drop_table('conversion_rules')

    # Remove enums
    op.execute("DROP TYPE IF EXISTS creditsourcetype")
    op.execute("DROP TYPE IF EXISTS xpsourcetype")
