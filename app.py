import os
import hashlib
import uuid
import json
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, send_file, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from extensions import db, migrate
from models import (
    User, Event, Order, Ticket, TransferRequest,
    Master, Review, BlockchainRecord
)
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)

    # ============================================
    # КОНТЕКСТНЫЙ ПРОЦЕССОР
    # ============================================
    @app.context_processor
    def inject_user():
        data = {
            'user_id': None,
            'user_username': None,
            'user_avatar': None,
            'user_role': None
        }
        if 'user_id' in session:
            user = db.session.get(User, session['user_id'])
            if user:
                data['user_id'] = user.id
                data['user_username'] = user.username
                data['user_avatar'] = user.avatar
                data['user_role'] = user.role
        return data

    # ============================================
    # ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
    # ============================================
    def get_qr_code(data):
        """Генерация QR-кода в base64"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    def generate_qr_hash():
        """Генерация уникального хеша для QR-кода"""
        return hashlib.sha256(f"{uuid.uuid4()}{datetime.now(timezone.utc).timestamp()}".encode()).hexdigest()

    # ============================================
    # ОСНОВНЫЕ МАРШРУТЫ
    # ============================================

    @app.route('/')
    def index():
        """Главная страница"""
        # Последние опубликованные мероприятия
        events = Event.query.filter_by(status='published').order_by(Event.date.asc()).limit(6).all()

        # Популярные мероприятия (по количеству билетов)
        popular_events = Event.query.filter_by(status='published').order_by(
            Event.total_tickets - Event.available_tickets
        ).limit(3).all()

        return render_template(
            'index.html',
            events=events,
            popular_events=popular_events
        )

    @app.route('/events')
    def events():
        """Страница всех мероприятий"""
        category = request.args.get('category')
        location = request.args.get('location')
        query = Event.query.filter_by(status='published')

        if category:
            query = query.filter_by(category=category)
        if location:
            query = query.filter_by(location=location)

        events = query.order_by(Event.date.asc()).all()
        return render_template('events.html', events=events)

    @app.route('/event/<int:event_id>')
    def event_detail(event_id):
        """Детальная страница мероприятия"""
        event = Event.query.get_or_404(event_id)

        # Проверяем, может ли пользователь купить билет
        can_buy = 'user_id' in session and event.status == 'published' and event.available_tickets > 0

        # Получаем отзывы организатора
        organizer_reviews = []
        if event.organizer.master:
            organizer_reviews = Review.query.filter_by(master_id=event.organizer.master.id).all()

        return render_template(
            'event_detail.html',
            event=event,
            can_buy=can_buy,
            organizer_reviews=organizer_reviews
        )

    @app.route('/event/<int:event_id>/buy', methods=['POST'])
    def buy_tickets(event_id):
        """Покупка билетов"""
        if 'user_id' not in session:
            flash('Войдите, чтобы купить билеты', 'error')
            return redirect(url_for('login'))

        event = Event.query.get_or_404(event_id)

        if event.status != 'published' or event.available_tickets <= 0:
            flash('Билеты на это мероприятие недоступны', 'error')
            return redirect(url_for('event_detail', event_id=event_id))

        quantity = request.form.get('quantity', type=int)
        if not quantity or quantity < 1:
            flash('Выберите количество билетов', 'error')
            return redirect(url_for('event_detail', event_id=event_id))

        if quantity > event.available_tickets:
            flash(f'Доступно только {event.available_tickets} билетов', 'error')
            return redirect(url_for('event_detail', event_id=event_id))

        # Создаём заказ
        order = Order(
            user_id=session['user_id'],
            event_id=event_id,
            quantity=quantity,
            total_price=event.price * quantity,
            status='paid'
        )
        db.session.add(order)
        db.session.flush()  # получаем order.id

        # Создаём билеты
        for _ in range(quantity):
            ticket = Ticket(
                event_id=event_id,
                order_id=order.id,
                owner_id=session['user_id'],
                qr_hash=generate_qr_hash(),
                status='active'
            )
            db.session.add(ticket)

        # Обновляем количество билетов
        event.available_tickets -= quantity

        db.session.commit()

        flash(f'Билеты успешно куплены! Количество: {quantity}', 'success')
        return redirect(url_for('my_tickets'))

    # ============================================
    # БИЛЕТЫ
    # ============================================

    @app.route('/tickets')
    def my_tickets():
        """Мои билеты"""
        if 'user_id' not in session:
            flash('Войдите, чтобы просмотреть билеты', 'error')
            return redirect(url_for('login'))

        tickets = Ticket.query.filter_by(owner_id=session['user_id']).all()
        return render_template('tickets.html', tickets=tickets)

    @app.route('/ticket/<int:ticket_id>/qr')
    def ticket_qr(ticket_id):
        """QR-код билета"""
        if 'user_id' not in session:
            abort(401)

        ticket = Ticket.query.get_or_404(ticket_id)

        if ticket.owner_id != session['user_id']:
            abort(403)

        qr_data = json.dumps({
            'ticket_id': ticket.id,
            'event_id': ticket.event_id,
            'qr_hash': ticket.qr_hash,
            'owner_id': ticket.owner_id
        })

        qr_base64 = get_qr_code(qr_data)
        return render_template('ticket_qr.html', ticket=ticket, qr_base64=qr_base64)

    @app.route('/ticket/<int:ticket_id>/transfer', methods=['GET', 'POST'])
    def transfer_ticket(ticket_id):
        """Передача билета другому пользователю"""
        if 'user_id' not in session:
            flash('Войдите, чтобы передать билет', 'error')
            return redirect(url_for('login'))

        ticket = Ticket.query.get_or_404(ticket_id)

        if ticket.owner_id != session['user_id']:
            abort(403)

        if ticket.status != 'active':
            flash('Этот билет нельзя передать', 'error')
            return redirect(url_for('my_tickets'))

        if request.method == 'POST':
            email = request.form.get('email')
            if not email:
                flash('Укажите email получателя', 'error')
                return redirect(url_for('transfer_ticket', ticket_id=ticket_id))

            recipient = User.query.filter_by(email=email).first()
            if not recipient:
                flash('Пользователь с таким email не найден', 'error')
                return redirect(url_for('transfer_ticket', ticket_id=ticket_id))

            if recipient.id == session['user_id']:
                flash('Нельзя передать билет самому себе', 'error')
                return redirect(url_for('transfer_ticket', ticket_id=ticket_id))

            # Создаём запрос на передачу
            request_transfer = TransferRequest(
                ticket_id=ticket.id,
                from_user_id=session['user_id'],
                to_user_id=recipient.id,
                status='pending'
            )
            db.session.add(request_transfer)
            db.session.commit()

            flash(f'Запрос на передачу билета отправлен пользователю {recipient.username}', 'success')
            return redirect(url_for('my_tickets'))

        return render_template('transfer_ticket.html', ticket=ticket)

    @app.route('/transfer/<int:request_id>/<action>', methods=['POST'])
    def handle_transfer(request_id, action):
        """Принятие или отклонение запроса на передачу билета"""
        if 'user_id' not in session:
            flash('Войдите', 'error')
            return redirect(url_for('login'))

        transfer = TransferRequest.query.get_or_404(request_id)

        if transfer.to_user_id != session['user_id']:
            abort(403)

        if transfer.status != 'pending':
            flash('Этот запрос уже обработан', 'error')
            return redirect(url_for('my_tickets'))

        if action == 'accept':
            # Принимаем передачу
            ticket = Ticket.query.get(transfer.ticket_id)
            ticket.owner_id = transfer.to_user_id
            ticket.status = 'transferred'
            ticket.transfer_to = transfer.to_user_id

            transfer.status = 'accepted'
            db.session.commit()
            flash('Билет успешно передан!', 'success')

        elif action == 'reject':
            transfer.status = 'rejected'
            db.session.commit()
            flash('Запрос на передачу отклонён', 'info')
        else:
            flash('Неверное действие', 'error')

        return redirect(url_for('my_tickets'))

    @app.route('/ticket/<int:ticket_id>/use', methods=['POST'])
    def use_ticket(ticket_id):
        """Отметка билета как использованного (для организаторов)"""
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        ticket = Ticket.query.get_or_404(ticket_id)
        event = Event.query.get(ticket.event_id)

        # Проверяем, что пользователь - организатор этого мероприятия
        if event.organizer_id != session['user_id']:
            return jsonify({'error': 'Forbidden'}), 403

        if ticket.status != 'active':
            return jsonify({'error': 'Ticket already used or invalid'}), 400

        ticket.status = 'used'
        db.session.commit()

        return jsonify({'success': True})

    # ============================================
    # МАРКЕТ МАСТЕРОВ
    # ============================================

    @app.route('/masters')
    def masters_list():
        """Список мастеров"""
        masters = Master.query.order_by(Master.rating.desc()).all()
        return render_template('master_list.html', masters=masters)

    @app.route('/master/<int:master_id>')
    def master_profile(master_id):
        """Профиль мастера"""
        master = Master.query.get_or_404(master_id)
        reviews = Review.query.filter_by(master_id=master_id).order_by(Review.created_at.desc()).all()

        can_review = False
        if 'user_id' in session and session['user_id'] != master.user_id:
            # Проверяем, не оставлял ли уже пользователь отзыв
            existing_review = Review.query.filter_by(
                master_id=master_id,
                reviewer_id=session['user_id']
            ).first()
            if not existing_review:
                can_review = True

        return render_template(
            'master_profile.html',
            master=master,
            reviews=reviews,
            can_review=can_review
        )

    @app.route('/master/<int:master_id>/review', methods=['POST'])
    def add_review(master_id):
        """Добавление отзыва мастеру"""
        if 'user_id' not in session:
            flash('Войдите, чтобы оставить отзыв', 'error')
            return redirect(url_for('login'))

        if session['user_id'] == master_id:
            flash('Нельзя оставить отзыв самому себе', 'error')
            return redirect(url_for('master_profile', master_id=master_id))

        rating = request.form.get('rating', type=int)
        comment = request.form.get('comment', '').strip()

        if not rating or rating < 1 or rating > 5:
            flash('Укажите оценку от 1 до 5', 'error')
            return redirect(url_for('master_profile', master_id=master_id))

        if not comment:
            flash('Напишите комментарий', 'error')
            return redirect(url_for('master_profile', master_id=master_id))

        master = Master.query.get_or_404(master_id)

        # Проверяем, не оставлял ли уже пользователь отзыв
        existing = Review.query.filter_by(
            master_id=master_id,
            reviewer_id=session['user_id']
        ).first()

        if existing:
            flash('Вы уже оставляли отзыв этому мастеру', 'error')
            return redirect(url_for('master_profile', master_id=master_id))

        review = Review(
            master_id=master_id,
            reviewer_id=session['user_id'],
            rating=rating,
            comment=comment
        )
        db.session.add(review)

        # Обновляем рейтинг мастера
        master.review_count += 1
        all_reviews = Review.query.filter_by(master_id=master_id).all()
        master.rating = sum(r.rating for r in all_reviews) / len(all_reviews)

        db.session.commit()

        flash('Отзыв добавлен!', 'success')
        return redirect(url_for('master_profile', master_id=master_id))

    # ============================================
    # БЛОКЧЕЙН
    # ============================================

    @app.route('/blockchain')
    def blockchain():
        """Страница блокчейн-гарантии"""
        if 'user_id' not in session:
            flash('Войдите, чтобы просмотреть блокчейн-записи', 'error')
            return redirect(url_for('login'))

        records = BlockchainRecord.query.filter_by(user_id=session['user_id']).order_by(
            BlockchainRecord.created_at.desc()
        ).all()

        return render_template('blockchain.html', records=records)

    @app.route('/blockchain/upload', methods=['POST'])
    def upload_reference():
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        file = request.files.get('file')
        description = request.form.get('description', '')

        if not file:
            return jsonify({'error': 'Файл не выбран'}), 400

        file_content = file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()

        record = BlockchainRecord(
            user_id=session['user_id'],
            record_type='reference',
            reference_hash=file_hash,
            blockchain_tx=f'0x{hashlib.sha256(f"{file_hash}{datetime.now(timezone.utc).timestamp()}".encode()).hexdigest()}',
            meta_data={
                'filename': secure_filename(file.filename),
                'description': description,
                'size': len(file_content)
            }
        )
        db.session.add(record)
        db.session.commit()

        flash('Референс успешно загружен в блокчейн!', 'success')
        return redirect(url_for('blockchain'))

    # ============================================
    # ПРОФИЛЬ
    # ============================================

    @app.route('/profile')
    def profile():
        """Страница профиля"""
        if 'user_id' not in session:
            flash('Войдите, чтобы просмотреть профиль', 'error')
            return redirect(url_for('login'))

        user = db.session.get(User, session['user_id'])

        # Получаем статистику
        total_tickets = Ticket.query.filter_by(owner_id=user.id).count()
        total_events = Event.query.filter_by(organizer_id=user.id).count()

        # Получаем запросы на передачу
        transfer_requests = TransferRequest.query.filter_by(to_user_id=user.id, status='pending').all()

        return render_template(
            'profile.html',
            user=user,
            total_tickets=total_tickets,
            total_events=total_events,
            transfer_requests=transfer_requests
        )

    @app.route('/profile/edit', methods=['GET', 'POST'])
    def edit_profile():
        """Редактирование профиля"""
        if 'user_id' not in session:
            flash('Войдите, чтобы редактировать профиль', 'error')
            return redirect(url_for('login'))

        user = db.session.get(User, session['user_id'])

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            bio = request.form.get('bio', '').strip()

            if not username:
                flash('Введите никнейм', 'error')
                return redirect(url_for('edit_profile'))

            # Проверка на уникальность никнейма
            existing = User.query.filter(User.username == username, User.id != user.id).first()
            if existing:
                flash('Этот никнейм уже занят', 'error')
                return redirect(url_for('edit_profile'))

            user.username = username
            user.bio = bio

            db.session.commit()
            flash('Профиль обновлён!', 'success')
            return redirect(url_for('profile'))

        return render_template('edit_profile.html', user=user)

    # ============================================
    # АУТЕНТИФИКАЦИЯ
    # ============================================

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if 'user_id' in session:
            return redirect(url_for('index'))

        if request.method == 'POST':
            login_input = request.form.get('login')
            password = request.form.get('password')

            if not login_input or not password:
                flash('Заполните все поля', 'error')
                return redirect(url_for('login'))

            user = User.query.filter(
                (User.email == login_input) | (User.username == login_input)
            ).first()

            if user and check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                flash('Вход выполнен!', 'success')
                return redirect(url_for('index'))

            flash('Неверный email/никнейм или пароль', 'error')

        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if 'user_id' in session:
            return redirect(url_for('index'))

        if request.method == 'POST':
            email = request.form.get('email')
            username = request.form.get('username')
            password = request.form.get('password')
            confirm = request.form.get('confirm_password')

            if not all([email, username, password, confirm]):
                flash('Заполните все поля', 'error')
                return redirect(url_for('register'))

            if password != confirm:
                flash('Пароли не совпадают', 'error')
                return redirect(url_for('register'))

            if len(password) < 4:
                flash('Пароль не менее 4 символов', 'error')
                return redirect(url_for('register'))

            if len(username) < 3:
                flash('Никнейм не менее 3 символов', 'error')
                return redirect(url_for('register'))

            if User.query.filter_by(email=email).first():
                flash('Email уже используется', 'error')
                return redirect(url_for('register'))

            if User.query.filter_by(username=username).first():
                flash('Никнейм уже занят', 'error')
                return redirect(url_for('register'))

            hashed = generate_password_hash(password)
            user = User(email=email, username=username, password_hash=hashed)
            db.session.add(user)
            db.session.commit()

            flash('Регистрация успешна! Войдите в аккаунт.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')

    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        flash('Вы вышли из аккаунта', 'info')
        return redirect(url_for('index'))

    # ============================================
    # СТАТИЧЕСКИЕ СТРАНИЦЫ
    # ============================================

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/help')
    def help_page():
        return render_template('help.html')

    @app.route('/rules')
    def rules():
        return render_template('rules.html')

    @app.route('/contacts')
    def contacts():
        return render_template('contacts.html')

    # ============================================
    # ОБРАБОТЧИКИ ОШИБОК
    # ============================================

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('500.html'), 500

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.config['DEBUG'])