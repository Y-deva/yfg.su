import os
import random
import time
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import create_app
from extensions import db
from models import User, Event, Order, Ticket, TransferRequest, Master, Review, BlockchainRecord

app = create_app()

# ============================================
# ДАННЫЕ ДЛЯ ГЕНЕРАЦИИ
# ============================================

USERNAMES = [
    'furry_fox', 'wolf_walker', 'dragon_master', 'cat_lover', 'bear_strong',
    'rabbit_jump', 'panda_cute', 'tiger_king', 'lion_heart', 'deer_grace',
    'racoon_master', 'owl_wise', 'eagle_eye', 'shark_fin', 'whale_song',
    'fox_tail', 'wolf_pack', 'dragon_fire', 'cat_claw', 'bear_hug',
    'rabbit_ears', 'panda_bear', 'tiger_stripe', 'lion_mane', 'deer_antler'
]

EVENT_TITLES = [
    "Фурри-вечеринка 'Хвостатый уикенд'",
    "Мастер-класс по созданию фурсьютов",
    "Выставка фурри-арта 'Мир зверей'",
    "Дискотека в зверином стиле",
    "Косплей-фестиваль 'Furry Fest'",
    "Онлайн-встреча фурри-сообщества",
    "Арт-колл 'Нарисуй своего персонажа'",
    "Карнавал в стиле фурри",
    "Фурри-конференция 'Тренды сообщества'",
    "Хвостатый забег (благотворительный)",
    "Мастерская по пошиву лап",
    "Фурри-квиз 'Угадай персонажа'",
    "Пикник в парке для фурри",
    "Новогодняя фурри-вечеринка",
    "Хэллоуин в зверином стиле",
    "Фотоконкурс 'Мой фурри-образ'",
    "Встреча художников-фурри",
    "Мастер-класс по цифровому рисунку",
    "Фурри-караоке",
    "Настольные игры в фурри-клубе"
]

EVENT_DESCRIPTIONS = [
    "Приглашаем всех на самую крутую фурри-вечеринку! Будут танцы, конкурсы и море позитива.",
    "Научитесь создавать свои собственные фурсьюты с нуля. Опытные мастера поделятся секретами.",
    "Выставка лучших фурри-художников. Более 100 работ в разных стилях.",
    "Зажигательная дискотека в стиле фурри. Лучшие треки и специальные гости.",
    "Крупнейший фестиваль косплея. Приходи в образе своего персонажа!",
    "Онлайн-встреча сообщества. Обсуждение новостей, планов и просто общение.",
    "Тематический арт-колл. Лучшие работы будут опубликованы в соцсетях.",
    "Яркий карнавал с шествием, конкурсами и призами.",
    "Ежегодная конференция фурри-сообщества. Спикеры, мастер-классы, нетворкинг.",
    "Благотворительный забег в костюмах животных. Помогаем приютам.",
    "Мастер-класс по изготовлению реалистичных лап и хвостов.",
    "Увлекательный квиз. Проверь свои знания фурри-вселенной.",
    "Уютный пикник с играми и общением в парке.",
    "Новогодняя вечеринка с Дедом Морозом-фурри.",
    "Страшный хэллоуин в зверином стиле. Костюмы обязательны.",
    "Конкурс фотографий в фурри-образах. Победителей ждут призы.",
    "Встреча для художников. Обмен опытом, советы, совместные проекты.",
    "Учимся создавать цифровые иллюстрации с нуля.",
    "Караоке-вечер. Исполняем песни в образах животных.",
    "Вечер настольных игр. Только для фурри-сообщества."
]

LOCATIONS = [
    'Москва', 'Санкт-Петербург', 'Екатеринбург', 'Новосибирск', 'Казань',
    'Нижний Новгород', 'Челябинск', 'Самара', 'Омск', 'Ростов-на-Дону',
    'Уфа', 'Красноярск', 'Пермь', 'Воронеж', 'Волгоград',
    'Краснодар', 'Саратов', 'Тюмень', 'Тольятти', 'Ижевск'
]

REVIEW_COMMENTS = [
    "Отличный мастер! Всё сделано качественно и в срок.",
    "Работа превзошла ожидания. Обязательно закажу ещё.",
    "Очень понравилось общаться с мастером. Внимательный и добрый.",
    "Качество просто супер! Рекомендую всем.",
    "Быстро, качественно, недорого. Идеальное сочетание.",
    "Мастер учёл все пожелания. Результат потрясающий.",
    "Отличная работа, буду рекомендовать друзьям.",
    "Немного задержали сроки, но работа стоит того.",
    "Всё отлично. Единственный минус - очередь.",
    "Мастер профессионал своего дела. Спасибо!"
]


# ============================================
# ФУНКЦИИ ГЕНЕРАЦИИ
# ============================================

def random_date(start_date, end_date):
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return start_date + timedelta(days=random_days)


def generate_unique_qr_hash():
    import hashlib
    import uuid
    return hashlib.sha256(f"{uuid.uuid4()}{time.time()}".encode()).hexdigest()


def inject_data():
    """Основная функция наполнения БД"""

    print("🚀 Запуск инжектора данных YFG")
    print("⚠️  ВНИМАНИЕ: БАЗА ДАННЫХ БУДЕТ ОЧИЩЕНА!")
    print("📁 Используется: SQLite")

    with app.app_context():
        # Очищаем базу вручную (удаляем все записи)
        db.session.query(BlockchainRecord).delete()
        db.session.query(Review).delete()
        db.session.query(Master).delete()
        db.session.query(TransferRequest).delete()
        db.session.query(Ticket).delete()
        db.session.query(Order).delete()
        db.session.query(Event).delete()
        db.session.query(User).delete()
        db.session.commit()
        print("✅ База данных очищена")

        # ============================================
        # 1. СОЗДАНИЕ ПОЛЬЗОВАТЕЛЕЙ
        # ============================================
        print("\n👤 Создание пользователей...")
        users = []

        # Админ
        admin = User(
            email='admin@yfg.ru',
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            bio='Главный администратор проекта YFG'
        )
        db.session.add(admin)
        users.append(admin)

        # Организаторы
        organizer_names = ['furry_organizer', 'event_master', 'party_planner']
        for i, name in enumerate(organizer_names):
            user = User(
                email=f'{name}@yfg.ru',
                username=name,
                password_hash=generate_password_hash('password123'),
                role='organizer',
                bio=f'Организатор фурри-мероприятий с {2019 + i}-летнем опытом.'
            )
            db.session.add(user)
            users.append(user)

        # Обычные пользователи
        for i, username in enumerate(USERNAMES[:20]):
            user = User(
                email=f'{username}@mail.ru',
                username=username,
                password_hash=generate_password_hash('password123'),
                role='user',
                bio=f'Фурри-энтузиаст, участник сообщества с {2020 + (i % 4)} года.'
            )
            db.session.add(user)
            users.append(user)

        db.session.commit()
        print(f"  ✅ Создано {len(users)} пользователей")

        # ============================================
        # 2. СОЗДАНИЕ МАСТЕРОВ
        # ============================================
        print("\n🎨 Создание мастеров...")
        masters = []

        master_users = users[5:15]  # возьмём часть пользователей как мастеров
        for i, user in enumerate(master_users):
            master = Master(
                user_id=user.id,
                description=f'Мастер по созданию фурсьютов и аксессуаров. Специализация: {random.choice(["персонажи", "аксессуары", "полные костюмы", "лапы и хвосты"])}.',
                portfolio=[],
                rating=random.uniform(3.5, 5.0),
                review_count=0
            )
            db.session.add(master)
            masters.append(master)

        db.session.commit()
        print(f"  ✅ Создано {len(masters)} мастеров")

        # ============================================
        # 3. СОЗДАНИЕ ОТЗЫВОВ
        # ============================================
        print("\n⭐ Создание отзывов...")

        for master in masters:
            # каждый мастер получает 2-5 отзывов
            num_reviews = random.randint(2, 5)
            reviewers = [u for u in users if u.id != master.user_id]

            for _ in range(min(num_reviews, len(reviewers))):
                reviewer = random.choice(reviewers)
                rating = random.randint(3, 5)
                comment = random.choice(REVIEW_COMMENTS)

                review = Review(
                    master_id=master.id,
                    reviewer_id=reviewer.id,
                    rating=rating,
                    comment=comment
                )
                db.session.add(review)

                # обновляем рейтинг мастера
                master.review_count += 1

        db.session.commit()
        print(f"  ✅ Создано {Review.query.count()} отзывов")

        # ============================================
        # 4. СОЗДАНИЕ МЕРОПРИЯТИЙ
        # ============================================
        print("\n📅 Создание мероприятий...")

        organizers = User.query.filter_by(role='organizer').all()
        events = []

        for i in range(20):
            organizer = random.choice(organizers)
            title = random.choice(EVENT_TITLES)

            # дата в будущем или прошлом
            if i < 10:
                date = random_date(datetime.now() - timedelta(days=30), datetime.now() - timedelta(days=1))
                status = 'completed'
            else:
                date = random_date(datetime.now() + timedelta(days=1), datetime.now() + timedelta(days=90))
                status = random.choice(['published', 'published', 'published', 'draft'])

            total_tickets = random.randint(30, 200)
            available_tickets = random.randint(0, total_tickets)

            event = Event(
                organizer_id=organizer.id,
                title=title,
                description=random.choice(EVENT_DESCRIPTIONS),
                category=random.choice(['встреча', 'концерт', 'выставка', 'конференция', 'вечеринка', 'соревнование']),
                date=date,
                location=random.choice(LOCATIONS),
                address=f'ул. {random.choice(["Ленина", "Пушкина", "Гагарина", "Мира", "Советская"])}, д. {random.randint(1, 99)}',
                price=random.randint(0, 5000),
                total_tickets=total_tickets,
                available_tickets=available_tickets,
                status=status
            )
            db.session.add(event)
            events.append(event)

        db.session.commit()
        print(f"  ✅ Создано {len(events)} мероприятий")

        # ============================================
        # 5. СОЗДАНИЕ ЗАКАЗОВ И БИЛЕТОВ
        # ============================================
        print("\n🎫 Создание заказов и билетов...")

        published_events = Event.query.filter_by(status='published').all()
        active_users = User.query.filter(User.role == 'user').all()

        orders = []
        tickets = []

        for event in published_events:
            num_orders = random.randint(0, 15)
            for _ in range(num_orders):
                if len(active_users) < 2:
                    continue
                buyer = random.choice(active_users)
                quantity = random.randint(1, 3)
                if event.available_tickets < quantity:
                    continue

                order = Order(
                    user_id=buyer.id,
                    event_id=event.id,
                    quantity=quantity,
                    total_price=event.price * quantity,
                    status='paid'
                )
                db.session.add(order)
                db.session.flush()
                orders.append(order)
                event.available_tickets -= quantity

                for _ in range(quantity):
                    ticket = Ticket(
                        event_id=event.id,
                        order_id=order.id,
                        owner_id=buyer.id,
                        qr_hash=generate_unique_qr_hash(),
                        status='active'
                    )
                    db.session.add(ticket)
                    tickets.append(ticket)

        db.session.commit()
        print(f"  ✅ Создано {len(orders)} заказов и {len(tickets)} билетов")

        # ============================================
        # 6. СОЗДАНИЕ ЗАПИСЕЙ В БЛОКЧЕЙНЕ
        # ============================================
        print("\n🔗 Создание блокчейн-записей...")

        for user in users[:5]:
            # запись о билете
            if user.tickets:
                ticket = user.tickets[0]
                record = BlockchainRecord(
                    user_id=user.id,
                    record_type='ticket',
                    reference_hash=ticket.qr_hash,
                    blockchain_tx=f'0x{random.randint(10 ** 15, 10 ** 16):x}',
                    meta_data={'event_id': ticket.event_id, 'ticket_id': ticket.id}
                )
                db.session.add(record)

            # запись о референсе (хеш изображения)
            if random.random() < 0.5:
                import hashlib
                fake_image_hash = hashlib.sha256(f"user_{user.id}_reference_{int(time.time())}".encode()).hexdigest()
                record = BlockchainRecord(
                    user_id=user.id,
                    record_type='reference',
                    reference_hash=fake_image_hash,
                    blockchain_tx=f'0x{random.randint(10 ** 15, 10 ** 16):x}',
                    meta_data={'filename': f'reference_{user.id}.png', 'description': 'Референс персонажа'}
                )
                db.session.add(record)

        db.session.commit()
        print(f"  ✅ Создано {BlockchainRecord.query.count()} блокчейн-записей")

        # ============================================
        # 7. СОЗДАНИЕ ЗАПРОСОВ НА ПЕРЕДАЧУ БИЛЕТОВ
        # ============================================
        print("\n🔄 Создание запросов на передачу билетов...")

        for ticket in tickets[:10]:
            if ticket.owner_id:
                possible_transfer = [u for u in active_users if u.id != ticket.owner_id]
                if possible_transfer and random.random() < 0.3:
                    to_user = random.choice(possible_transfer)
                    request = TransferRequest(
                        ticket_id=ticket.id,
                        from_user_id=ticket.owner_id,
                        to_user_id=to_user.id,
                        status=random.choice(['pending', 'accepted', 'rejected'])
                    )
                    db.session.add(request)

                    if request.status == 'accepted':
                        ticket.owner_id = to_user.id
                        ticket.status = 'transferred'
                        ticket.transfer_to = to_user.id

        db.session.commit()
        print(f"  ✅ Создано {TransferRequest.query.count()} запросов на передачу")

        # ============================================
        # ИТОГИ
        # ============================================
        print("\n" + "=" * 50)
        print("🎉 БАЗА ДАННЫХ УСПЕШНО НАПОЛНЕНА!")
        print("=" * 50)
        print(f"👤 Пользователей: {User.query.count()}")
        print(f"📅 Мероприятий: {Event.query.count()}")
        print(f"📦 Заказов: {Order.query.count()}")
        print(f"🎫 Билетов: {Ticket.query.count()}")
        print(f"🎨 Мастеров: {Master.query.count()}")
        print(f"⭐ Отзывов: {Review.query.count()}")
        print(f"🔗 Блокчейн-записей: {BlockchainRecord.query.count()}")
        print(f"🔄 Запросов на передачу: {TransferRequest.query.count()}")
        print("=" * 50)
        print("✅ Готово к использованию!")


if __name__ == '__main__':
    print("🚀 ЗАПУСК ИНЖЕКТОРА ДАННЫХ YFG")
    inject_data()