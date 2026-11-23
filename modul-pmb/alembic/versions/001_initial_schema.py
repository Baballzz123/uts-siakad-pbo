"""Initial PMB Schema

Revision ID: 001_pmb
Revises: 
Create Date: 2026-11-13
"""
from alembic import op
import sqlalchemy as sa

revision = '001_pmb'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'program_studi',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('kode', sa.String(length=3), nullable=False, unique=True),
        sa.Column('nama', sa.String(length=100), nullable=False),
        sa.Column('fakultas', sa.String(length=100), nullable=False),
    )
    op.create_table(
        'jalur_masuk',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nama_jalur', sa.Enum('SNBP', 'SNBT', 'MANDIRI', name='jalurmasukenm'), nullable=False, unique=True),
        sa.Column('kuota', sa.Integer(), nullable=True),
    )
    op.create_table(
        'calon_mahasiswa',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nim', sa.String(length=12), nullable=True, unique=True),
        sa.Column('nama_lengkap', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=150), nullable=False, unique=True),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('tanggal_lahir', sa.Date(), nullable=False),
        sa.Column('alamat', sa.String(length=255), nullable=False),
        sa.Column('program_studi_id', sa.Integer(), sa.ForeignKey('program_studi.id'), nullable=False),
        sa.Column('jalur_masuk_id', sa.Integer(), sa.ForeignKey('jalur_masuk.id'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='statuspendaftaran'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("phone LIKE '08%' OR phone LIKE '+628%'", name="check_phone_id"),
        sa.CheckConstraint("email LIKE '%_@__%.__%'", name="check_email_format"),
    )

def downgrade() -> None:
    # Rollback menghapus tabel secara berurutan agar tidak melanggar Foreign Key
    op.drop_table('calon_mahasiswa')
    op.drop_table('jalur_masuk')
    op.drop_table('program_studi')