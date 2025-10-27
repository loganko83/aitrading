Create all database tables from SQLAlchemy models
import sys
sys.path.insert(0, '/mnt/storage/trading/trading-backend')

from app.database.session import engine
from app.database.base import Base

# Import all models to register them with Base
from app.models.user import User, Session, Account, XpTransaction
from app.models.api_key import ApiKey
from app.models.trading import Trade, Position, TradingSettings, StrategyConfig
from app.models.webhook import Webhook
from app.models.telegram_config import TelegramConfig

print('Creating all tables from models...')
Base.metadata.create_all(bind=engine)
print('✓ All tables created successfully!')

# List created tables
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f'\nCreated tables ({len(tables)}):')
for table in sorted(tables):
    print(f'  - {table}')
