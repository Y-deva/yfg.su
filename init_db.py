import os
from app import create_app
from extensions import db
from models import User, Event, Order, Ticket, TransferRequest, Master, Review, BlockchainRecord

app = create_app()

with app.app_context():
    # Создаём таблицы, если их нет
    db.create_all()
    print("✅ База данных создана")
    print(f"   Путь: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("\n📋 Созданы таблицы:")
    print("  - users")
    print("  - events")
    print("  - orders")
    print("  - tickets")
    print("  - transfer_requests")
    print("  - masters")
    print("  - reviews")
    print("  - blockchain_records")