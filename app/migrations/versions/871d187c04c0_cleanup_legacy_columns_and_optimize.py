"""cleanup_legacy_columns_and_optimize

Migracja usuwa legacy kolumny i optymalizuje strukturę:
1. Usuwa User.role (duplikat account_type)
2. Usuwa User.event_id (używamy EventRegistration)
3. Usuwa User.group_id (używamy UserGroupMember)
4. Usuwa tabelę default_email_templates (redundancja)
5. Dodaje indeksy dla wydajności

Revision ID: 871d187c04c0
Revises: b8f996496580
Create Date: 2025-10-10 09:04:31.449014

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '871d187c04c0'
down_revision = 'b8f996496580'
branch_labels = None
depends_on = None


def upgrade():
    """Migracja do przodu"""
    
    # Krok 0: Dodaj nowe kolumny (slug, uuid)
    print("📋 Krok 0: Dodawanie nowych kolumn")
    
    # Dodaj slug do event_schedule
    op.add_column('event_schedule', sa.Column('slug', sa.String(length=200), nullable=True))
    op.create_index('ix_event_schedule_slug', 'event_schedule', ['slug'], unique=True)
    
    # Generuj slugi dla istniejących wydarzeń
    op.execute("""
        UPDATE event_schedule
        SET slug = LOWER(
            REPLACE(
                REPLACE(
                    REPLACE(title, ' ', '-'),
                    'ą', 'a'
                ),
                'ę', 'e'
            ) || '-' || id
        )
        WHERE slug IS NULL
    """)
    
    # Krok 1: Migruj użytkowników z User.event_id do EventRegistration
    print("📋 Krok 1: Migracja User.event_id → EventRegistration")
    op.execute("""
        INSERT INTO event_registrations (user_id, event_id, registration_date, is_active, registration_source)
        SELECT id, event_id, created_at, is_active, 'legacy_migration'
        FROM users
        WHERE event_id IS NOT NULL
        ON CONFLICT (user_id, event_id) DO NOTHING
    """)
    
    # Krok 2: Migruj użytkowników z User.group_id do UserGroupMember
    print("📋 Krok 2: Migracja User.group_id → UserGroupMember")
    op.execute("""
        INSERT INTO user_group_members (group_id, user_id, is_active, member_type, created_at)
        SELECT group_id, id, is_active, 'user', created_at
        FROM users
        WHERE group_id IS NOT NULL
        ON CONFLICT DO NOTHING
    """)
    
    # Krok 3: Synchronizuj User.role z User.account_type (na wypadek inconsistency)
    print("📋 Krok 3: Synchronizacja User.role → User.account_type")
    op.execute("""
        UPDATE users
        SET role = account_type
        WHERE role != account_type
    """)
    
    # Krok 4: Usuń kolumny legacy z tabeli users
    print("📋 Krok 4: Usuwanie legacy kolumn z users")
    op.drop_constraint('users_event_id_fkey', 'users', type_='foreignkey')
    op.drop_constraint('users_group_id_fkey', 'users', type_='foreignkey')
    op.drop_column('users', 'role')
    op.drop_column('users', 'event_id')
    op.drop_column('users', 'group_id')
    
    # Krok 5: Usuń tabelę default_email_templates (redundancja)
    print("📋 Krok 5: Usuwanie tabeli default_email_templates")
    op.drop_table('default_email_templates')
    
    # Krok 6: Dodaj indeksy dla wydajności
    print("📋 Krok 6: Dodawanie indeksów")
    
    # Sprawdź czy indeks już istnieje, jeśli nie - dodaj
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # EmailQueue.campaign_id
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('email_queue')]
    if 'ix_email_queue_campaign_id' not in existing_indexes:
        op.create_index('ix_email_queue_campaign_id', 'email_queue', ['campaign_id'])
    
    # EmailLog.campaign_id
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('email_logs')]
    if 'ix_email_logs_campaign_id' not in existing_indexes:
        op.create_index('ix_email_logs_campaign_id', 'email_logs', ['campaign_id'])
    
    # Call.campaign_id
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('crm_calls')]
    if 'ix_crm_calls_campaign_id' not in existing_indexes:
        op.create_index('ix_crm_calls_campaign_id', 'crm_calls', ['campaign_id'])
    
    print("✅ Migracja zakończona pomyślnie!")


def downgrade():
    """Migracja wstecz (przywrócenie legacy kolumn)"""
    
    # Krok 0: Usuń nowe kolumny
    print("📋 Krok 0: Usuwanie nowych kolumn")
    op.drop_index('ix_event_schedule_slug', table_name='event_schedule')
    op.drop_column('event_schedule', 'slug')
    
    # Krok 1: Usuwanie indeksów
    print("📋 Krok 1: Usuwanie indeksów")
    op.drop_index('ix_crm_calls_campaign_id', table_name='crm_calls')
    op.drop_index('ix_email_logs_campaign_id', table_name='email_logs')
    op.drop_index('ix_email_queue_campaign_id', table_name='email_queue')
    
    # Krok 2: Przywróć tabelę default_email_templates
    print("📋 Krok 2: Przywracanie tabeli default_email_templates")
    op.create_table('default_email_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('template_type', sa.String(length=50), nullable=False),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('html_content', sa.Text(), nullable=True),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('variables', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Krok 3: Przywróć kolumny legacy w users
    print("📋 Krok 3: Przywracanie legacy kolumn w users")
    op.add_column('users', sa.Column('role', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('event_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('group_id', sa.Integer(), nullable=True))
    
    # Przywróć foreign keys
    op.create_foreign_key('users_event_id_fkey', 'users', 'event_schedule', ['event_id'], ['id'])
    op.create_foreign_key('users_group_id_fkey', 'users', 'user_groups', ['group_id'], ['id'])
    
    # Krok 4: Migruj dane z powrotem (z EventRegistration do User.event_id)
    print("📋 Krok 4: Migracja EventRegistration → User.event_id")
    op.execute("""
        UPDATE users
        SET event_id = (
            SELECT event_id
            FROM event_registrations
            WHERE event_registrations.user_id = users.id
            AND event_registrations.is_active = TRUE
            LIMIT 1
        )
        WHERE account_type = 'event_registration'
    """)
    
    # Krok 5: Migruj dane z powrotem (z UserGroupMember do User.group_id)
    print("📋 Krok 5: Migracja UserGroupMember → User.group_id")
    op.execute("""
        UPDATE users
        SET group_id = (
            SELECT group_id
            FROM user_group_members
            WHERE user_group_members.user_id = users.id
            AND user_group_members.is_active = TRUE
            LIMIT 1
        )
    """)
    
    # Krok 6: Synchronizuj account_type → role
    print("📋 Krok 6: Synchronizacja account_type → role")
    op.execute("""
        UPDATE users
        SET role = account_type
    """)
    
    print("✅ Downgrade zakończony!")
