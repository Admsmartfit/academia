"""Add Split Bancario module

Revision ID: b5e8f9a1c2d3
Revises: 3dad790c25ad
Create Date: 2025-02-05

Adiciona tabelas e campos para o modulo de Split Bancario Dinamico:
- Tabela collaborator_bank_info: Dados bancarios dos colaboradores
- Tabela split_configurations: Configuracao de split por horario
- Tabela commission_entries: Registro de comissoes
- Tabela payout_batches: Lotes de pagamento
- Tabela split_settings: Configuracoes globais
- Campo professional_type em users
- Campo base_commission_rate em users
- Campo current_split_rate em class_schedules
- Campo avg_occupancy_rate em class_schedules
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5e8f9a1c2d3'
down_revision = '3dad790c25ad'
branch_labels = None
depends_on = None


def upgrade():
    # Enum types
    professional_type_enum = sa.Enum('instructor', 'technician', 'nutritionist', name='professionaltype')
    commission_status_enum = sa.Enum('pending', 'approved', 'paid', 'cancelled', name='commissionstatus')
    payout_status_enum = sa.Enum('draft', 'pending', 'approved', 'processing', 'paid', 'failed', name='payoutstatus')
    demand_level_enum = sa.Enum('low', 'standard', 'high', name='demandlevel')

    # Create enums
    professional_type_enum.create(op.get_bind(), checkfirst=True)
    commission_status_enum.create(op.get_bind(), checkfirst=True)
    payout_status_enum.create(op.get_bind(), checkfirst=True)
    demand_level_enum.create(op.get_bind(), checkfirst=True)

    # Add columns to users
    op.add_column('users', sa.Column('professional_type', professional_type_enum, nullable=True))
    op.add_column('users', sa.Column('base_commission_rate', sa.Numeric(5, 2), nullable=True))

    # Add columns to class_schedules
    op.add_column('class_schedules', sa.Column('current_split_rate', sa.Numeric(5, 2), server_default='60.00', nullable=True))
    op.add_column('class_schedules', sa.Column('avg_occupancy_rate', sa.Numeric(5, 2), server_default='0.00', nullable=True))

    # Create collaborator_bank_info table
    op.create_table('collaborator_bank_info',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), unique=True, nullable=False),
        sa.Column('bank_code', sa.String(10), nullable=True),
        sa.Column('bank_name', sa.String(100), nullable=True),
        sa.Column('agency', sa.String(10), nullable=True),
        sa.Column('account_number', sa.String(20), nullable=True),
        sa.Column('account_type', sa.String(20), nullable=True),
        sa.Column('account_holder_name', sa.String(200), nullable=True),
        sa.Column('account_holder_cpf', sa.String(14), nullable=True),
        sa.Column('pix_key_type', sa.String(20), nullable=True),
        sa.Column('pix_key', sa.String(100), nullable=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Create split_settings table
    op.create_table('split_settings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('credit_value_reais', sa.Numeric(10, 2), server_default='15.00'),
        sa.Column('low_demand_academy_pct', sa.Numeric(5, 2), server_default='20.00'),
        sa.Column('low_demand_professional_pct', sa.Numeric(5, 2), server_default='80.00'),
        sa.Column('standard_demand_academy_pct', sa.Numeric(5, 2), server_default='40.00'),
        sa.Column('standard_demand_professional_pct', sa.Numeric(5, 2), server_default='60.00'),
        sa.Column('high_demand_academy_pct', sa.Numeric(5, 2), server_default='60.00'),
        sa.Column('high_demand_professional_pct', sa.Numeric(5, 2), server_default='40.00'),
        sa.Column('low_demand_threshold', sa.Numeric(5, 2), server_default='40.00'),
        sa.Column('high_demand_threshold', sa.Numeric(5, 2), server_default='80.00'),
        sa.Column('suggestion_job_enabled', sa.Boolean(), default=True),
        sa.Column('suggestion_lookback_days', sa.Integer(), server_default='30'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('updated_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True)
    )

    # Create split_configurations table
    op.create_table('split_configurations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('schedule_id', sa.Integer(), sa.ForeignKey('class_schedules.id'), nullable=False),
        sa.Column('academy_percentage', sa.Numeric(5, 2), server_default='40.00'),
        sa.Column('professional_percentage', sa.Numeric(5, 2), server_default='60.00'),
        sa.Column('demand_level', demand_level_enum, server_default='standard'),
        sa.Column('occupancy_rate', sa.Numeric(5, 2), server_default='0.00'),
        sa.Column('suggested_academy_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('suggested_professional_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('suggested_demand_level', demand_level_enum, nullable=True),
        sa.Column('suggestion_pending', sa.Boolean(), default=False),
        sa.Column('suggested_at', sa.DateTime(), nullable=True),
        sa.Column('is_manual_override', sa.Boolean(), default=False),
        sa.Column('effective_from', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Create payout_batches table
    op.create_table('payout_batches',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('professional_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('reference_month', sa.Integer(), nullable=False),
        sa.Column('reference_year', sa.Integer(), nullable=False),
        sa.Column('total_gross', sa.Numeric(10, 2), server_default='0.00'),
        sa.Column('total_academy', sa.Numeric(10, 2), server_default='0.00'),
        sa.Column('total_professional', sa.Numeric(10, 2), server_default='0.00'),
        sa.Column('entries_count', sa.Integer(), server_default='0'),
        sa.Column('status', payout_status_enum, server_default='draft'),
        sa.Column('approved_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('payment_reference', sa.String(100), nullable=True),
        sa.Column('payment_proof_url', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Create commission_entries table
    op.create_table('commission_entries',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('booking_id', sa.Integer(), sa.ForeignKey('bookings.id'), nullable=False),
        sa.Column('professional_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('credit_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('academy_percentage', sa.Numeric(5, 2), nullable=False),
        sa.Column('professional_percentage', sa.Numeric(5, 2), nullable=False),
        sa.Column('amount_academy', sa.Numeric(10, 2), nullable=False),
        sa.Column('amount_professional', sa.Numeric(10, 2), nullable=False),
        sa.Column('booking_status', sa.String(20), nullable=True),
        sa.Column('professional_type', professional_type_enum, nullable=True),
        sa.Column('demand_level', demand_level_enum, nullable=True),
        sa.Column('status', commission_status_enum, server_default='pending'),
        sa.Column('payout_batch_id', sa.Integer(), sa.ForeignKey('payout_batches.id'), nullable=True),
        sa.Column('processed_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # Create indexes
    op.create_index('ix_commission_entries_professional_id', 'commission_entries', ['professional_id'])
    op.create_index('ix_commission_entries_status', 'commission_entries', ['status'])
    op.create_index('ix_payout_batches_professional_id', 'payout_batches', ['professional_id'])
    op.create_index('ix_payout_batches_status', 'payout_batches', ['status'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_payout_batches_status', table_name='payout_batches')
    op.drop_index('ix_payout_batches_professional_id', table_name='payout_batches')
    op.drop_index('ix_commission_entries_status', table_name='commission_entries')
    op.drop_index('ix_commission_entries_professional_id', table_name='commission_entries')

    # Drop tables
    op.drop_table('commission_entries')
    op.drop_table('payout_batches')
    op.drop_table('split_configurations')
    op.drop_table('split_settings')
    op.drop_table('collaborator_bank_info')

    # Remove columns from class_schedules
    op.drop_column('class_schedules', 'avg_occupancy_rate')
    op.drop_column('class_schedules', 'current_split_rate')

    # Remove columns from users
    op.drop_column('users', 'base_commission_rate')
    op.drop_column('users', 'professional_type')

    # Drop enums
    sa.Enum(name='demandlevel').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='payoutstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='commissionstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='professionaltype').drop(op.get_bind(), checkfirst=True)
