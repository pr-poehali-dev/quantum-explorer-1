import json
import os
import hmac
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import psycopg2

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Session-Id, X-Auth-Token',
    'Access-Control-Max-Age': '86400',
}

def verify_token(token: str):
    if not token:
        return None
    try:
        parts = token.split(':', 1)
        if len(parts) != 2:
            return None
        user_id = int(parts[0])
        token_sig = parts[1]
        expected_hash = hmac.new(
            os.environ['SECRET_KEY'].encode('utf-8'),
            token_sig.encode('utf-8'),
            'sha256'
        ).hexdigest()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, email, name, token_hash FROM users WHERE id = %s AND email_verified = TRUE", (user_id,))
        row = cur.fetchone()
        conn.close()
        if not row or not row[3]:
            return None
        if not hmac.compare_digest(expected_hash, row[3]):
            return None
        return {'id': row[0], 'email': row[1], 'name': row[2]}
    except Exception:
        return None

def get_db():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def send_order_email(to_email: str, order_id: int, name: str, address: str, phone: str, comment: str, items: list, total: int):
    """Отправка email клиенту об успешном оформлении заказа"""
    smtp_user = os.environ.get('SMTP_USER', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))

    if not smtp_user or not smtp_password:
        print('SMTP credentials not configured, skipping email')
        return

    # Формируем список товаров для письма
    items_rows = ''
    for item in items:
        item_total = item['price'] * item['qty']
        items_rows += f"""
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;">{item['name']}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:center;">{item['qty']} шт.</td>
            <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right;">{item['price']:,} ₽</td>
            <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right;font-weight:600;">{item_total:,} ₽</td>
        </tr>"""

    comment_block = f"""
        <tr>
            <td colspan="2" style="padding:6px 0;color:#666;">Комментарий:</td>
            <td colspan="2" style="padding:6px 0;">{comment}</td>
        </tr>""" if comment else ''

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:32px 0;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                    <!-- Header -->
                    <tr>
                        <td style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:32px 40px;text-align:center;">
                            <h1 style="margin:0;color:#ffffff;font-size:24px;font-weight:700;">✅ Заказ успешно оформлен!</h1>
                            <p style="margin:8px 0 0;color:rgba(255,255,255,0.85);font-size:15px;">Заказ №{order_id}</p>
                        </td>
                    </tr>
                    <!-- Body -->
                    <tr>
                        <td style="padding:32px 40px;">
                            <p style="margin:0 0 24px;font-size:16px;color:#333;">Здравствуйте, <strong>{name}</strong>!</p>
                            <p style="margin:0 0 24px;font-size:15px;color:#555;line-height:1.6;">
                                Ваш заказ принят и уже передан в обработку. Мы свяжемся с вами в ближайшее время для подтверждения.
                            </p>

                            <!-- Order details -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;background:#f9f9fb;border-radius:8px;padding:0;overflow:hidden;">
                                <tr style="background:#f0f0f5;">
                                    <td colspan="4" style="padding:10px 12px;font-size:13px;font-weight:700;color:#444;text-transform:uppercase;letter-spacing:0.5px;">Ваши данные</td>
                                </tr>
                                <tr>
                                    <td colspan="2" style="padding:6px 12px;color:#666;width:140px;">Получатель:</td>
                                    <td colspan="2" style="padding:6px 12px;font-weight:600;">{name}</td>
                                </tr>
                                <tr>
                                    <td colspan="2" style="padding:6px 12px;color:#666;">Телефон:</td>
                                    <td colspan="2" style="padding:6px 12px;">{phone}</td>
                                </tr>
                                <tr>
                                    <td colspan="2" style="padding:6px 12px;color:#666;">Адрес:</td>
                                    <td colspan="2" style="padding:6px 12px;">{address}</td>
                                </tr>
                                {comment_block}
                            </table>

                            <!-- Items table -->
                            <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:#333;">Состав заказа:</p>
                            <table width="100%" cellpadding="0" cellspacing="0" style="border-radius:8px;overflow:hidden;border:1px solid #eee;">
                                <tr style="background:#f0f0f5;">
                                    <th style="padding:10px 12px;text-align:left;font-size:13px;color:#444;">Товар</th>
                                    <th style="padding:10px 12px;text-align:center;font-size:13px;color:#444;">Кол-во</th>
                                    <th style="padding:10px 12px;text-align:right;font-size:13px;color:#444;">Цена</th>
                                    <th style="padding:10px 12px;text-align:right;font-size:13px;color:#444;">Сумма</th>
                                </tr>
                                {items_rows}
                                <tr style="background:#f9f9fb;">
                                    <td colspan="3" style="padding:12px;text-align:right;font-weight:700;font-size:15px;color:#333;">Итого:</td>
                                    <td style="padding:12px;text-align:right;font-weight:700;font-size:16px;color:#6366f1;">{total:,} ₽</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding:20px 40px 32px;text-align:center;color:#aaa;font-size:13px;">
                            Это письмо отправлено автоматически. Пожалуйста, не отвечайте на него.
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'✅ Заказ №{order_id} успешно оформлен'
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())
        print(f'Order confirmation email sent to {to_email}')
    except Exception as e:
        print(f'Failed to send email to {to_email}: {e}')

def send_manager_notification(order_id: int, name: str, phone: str, address: str, comment: str, items: list, total: int):
    """Отправка уведомления менеджерам о новом заказе"""
    smtp_user = os.environ.get('SMTP_USER', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))

    if not smtp_user or not smtp_password:
        print('SMTP credentials not configured, skipping manager notification')
        return

    # Получаем список email менеджеров из БД
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT email, name FROM managers ORDER BY id")
        managers = cur.fetchall()
        conn.close()
    except Exception as e:
        print(f'Failed to fetch managers: {e}')
        return

    if not managers:
        print('No managers found, skipping notification')
        return

    # Формируем список товаров для письма
    items_rows = ''
    for item in items:
        item_total = item['price'] * item['qty']
        items_rows += f"""
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;">{item['name']}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:center;">{item['qty']} шт.</td>
            <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right;">{item['price']:,} ₽</td>
            <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right;font-weight:600;">{item_total:,} ₽</td>
        </tr>"""

    comment_block = f"""
        <tr>
            <td colspan="2" style="padding:6px 12px;color:#666;">Комментарий:</td>
            <td colspan="2" style="padding:6px 12px;">{comment}</td>
        </tr>""" if comment else ''

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:32px 0;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                    <!-- Header -->
                    <tr>
                        <td style="background:linear-gradient(135deg,#f59e0b,#ef4444);padding:32px 40px;text-align:center;">
                            <h1 style="margin:0;color:#ffffff;font-size:24px;font-weight:700;">🛒 Новый заказ!</h1>
                            <p style="margin:8px 0 0;color:rgba(255,255,255,0.9);font-size:15px;">Заказ №{order_id} ожидает обработки</p>
                        </td>
                    </tr>
                    <!-- Body -->
                    <tr>
                        <td style="padding:32px 40px;">
                            <!-- Order details -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;background:#f9f9fb;border-radius:8px;overflow:hidden;">
                                <tr style="background:#f0f0f5;">
                                    <td colspan="4" style="padding:10px 12px;font-size:13px;font-weight:700;color:#444;text-transform:uppercase;letter-spacing:0.5px;">Данные покупателя</td>
                                </tr>
                                <tr>
                                    <td colspan="2" style="padding:6px 12px;color:#666;width:140px;">Получатель:</td>
                                    <td colspan="2" style="padding:6px 12px;font-weight:600;">{name}</td>
                                </tr>
                                <tr>
                                    <td colspan="2" style="padding:6px 12px;color:#666;">Телефон:</td>
                                    <td colspan="2" style="padding:6px 12px;font-weight:600;">{phone}</td>
                                </tr>
                                <tr>
                                    <td colspan="2" style="padding:6px 12px;color:#666;">Адрес:</td>
                                    <td colspan="2" style="padding:6px 12px;">{address}</td>
                                </tr>
                                {comment_block}
                            </table>

                            <!-- Items table -->
                            <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:#333;">Состав заказа:</p>
                            <table width="100%" cellpadding="0" cellspacing="0" style="border-radius:8px;overflow:hidden;border:1px solid #eee;">
                                <tr style="background:#f0f0f5;">
                                    <th style="padding:10px 12px;text-align:left;font-size:13px;color:#444;">Товар</th>
                                    <th style="padding:10px 12px;text-align:center;font-size:13px;color:#444;">Кол-во</th>
                                    <th style="padding:10px 12px;text-align:right;font-size:13px;color:#444;">Цена</th>
                                    <th style="padding:10px 12px;text-align:right;font-size:13px;color:#444;">Сумма</th>
                                </tr>
                                {items_rows}
                                <tr style="background:#f9f9fb;">
                                    <td colspan="3" style="padding:12px;text-align:right;font-weight:700;font-size:15px;color:#333;">Итого:</td>
                                    <td style="padding:12px;text-align:right;font-weight:700;font-size:16px;color:#ef4444;">{total:,} ₽</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding:20px 40px 32px;text-align:center;color:#aaa;font-size:13px;">
                            Это автоматическое уведомление для менеджеров. Войдите в панель администратора для обработки заказа.
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

    manager_emails = [m[0] for m in managers]
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🛒 Новый заказ №{order_id} — {name}'
        msg['From'] = smtp_user
        msg['To'] = ', '.join(manager_emails)
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, manager_emails, msg.as_string())
        print(f'Manager notification sent to {manager_emails}')
    except Exception as e:
        print(f'Failed to send manager notification: {e}')


def handler(event: dict, context) -> dict:
    """Магазин: товары, корзина, заказы. Корзина — по session_id, заказы — требуют авторизации."""
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}

    method = event.get('httpMethod', 'GET')
    params = event.get('queryStringParameters') or {}
    action = params.get('action', '')
    body = {}
    if event.get('body'):
        body = json.loads(event['body'])

    headers = event.get('headers', {})
    session_id = headers.get('X-Session-Id') or headers.get('x-session-id', '')
    token = headers.get('X-Auth-Token') or headers.get('x-auth-token', '')
    current_user = verify_token(token) if token else None

    # GET ?action=products
    if method == 'GET' and action == 'products':
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, description, price, emoji, image_url, button_class, in_stock FROM products WHERE in_stock = TRUE ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        products = [{'id': r[0], 'name': r[1], 'description': r[2], 'price': r[3], 'emoji': r[4], 'image_url': r[5], 'button_class': r[6], 'in_stock': r[7]} for r in rows]
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'products': products})}

    # GET ?action=cart
    if method == 'GET' and action == 'cart':
        if not session_id:
            return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'items': []})}
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT ci.id, ci.quantity, p.id, p.name, p.price, p.emoji, p.image_url
            FROM cart_items ci JOIN products p ON ci.product_id = p.id
            WHERE ci.session_id = %s
        """, (session_id,))
        rows = cur.fetchall()
        conn.close()
        items = [{'cart_id': r[0], 'quantity': r[1], 'product_id': r[2], 'name': r[3], 'price': r[4], 'emoji': r[5], 'image_url': r[6]} for r in rows]
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'items': items})}

    # POST ?action=cart
    if method == 'POST' and action == 'cart':
        if not session_id:
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'session_id обязателен'})}
        product_id = body.get('product_id')
        quantity = int(body.get('quantity', 1))
        if not product_id:
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'product_id обязателен'})}
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO cart_items (session_id, product_id, quantity)
            VALUES (%s, %s, %s)
            ON CONFLICT (session_id, product_id)
            DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity
        """, (session_id, product_id, quantity))
        conn.commit()
        conn.close()
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'ok': True})}

    # PUT ?action=cart
    if method == 'PUT' and action == 'cart':
        if not session_id:
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'session_id обязателен'})}
        product_id = body.get('product_id')
        quantity = int(body.get('quantity', 1))
        conn = get_db()
        cur = conn.cursor()
        if quantity <= 0:
            cur.execute("DELETE FROM cart_items WHERE session_id=%s AND product_id=%s", (session_id, product_id))
        else:
            cur.execute("UPDATE cart_items SET quantity=%s WHERE session_id=%s AND product_id=%s", (quantity, session_id, product_id))
        conn.commit()
        conn.close()
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'ok': True})}

    # POST ?action=orders
    if method == 'POST' and action == 'orders':
        if not current_user:
            return {'statusCode': 401, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Войдите в аккаунт для оформления заказа'})}
        if not session_id:
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'session_id обязателен'})}
        name = body.get('name', current_user.get('name', ''))
        phone = body.get('phone', '')
        address = body.get('address', '')
        comment = body.get('comment', '')
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT ci.quantity, p.id, p.name, p.price
            FROM cart_items ci JOIN products p ON ci.product_id = p.id
            WHERE ci.session_id = %s
        """, (session_id,))
        cart = cur.fetchall()
        if not cart:
            conn.close()
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Корзина пуста'})}
        total = sum(r[0] * r[3] for r in cart)
        cur.execute(
            "INSERT INTO orders (user_id, total, name, phone, address, comment) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (current_user['id'], total, name, phone, address, comment)
        )
        order_id = cur.fetchone()[0]
        for qty, pid, pname, pprice in cart:
            cur.execute("INSERT INTO order_items (order_id, product_id, product_name, product_price, quantity) VALUES (%s, %s, %s, %s, %s)",
                        (order_id, pid, pname, pprice, qty))
        cur.execute("DELETE FROM cart_items WHERE session_id=%s", (session_id,))
        conn.commit()
        conn.close()

        email_items = [{'name': pname, 'price': pprice, 'qty': qty} for qty, pid, pname, pprice in cart]
        send_order_email(
            to_email=current_user['email'],
            order_id=order_id,
            name=name,
            address=address,
            phone=phone,
            comment=comment,
            items=email_items,
            total=total
        )
        send_manager_notification(
            order_id=order_id,
            name=name,
            phone=phone,
            address=address,
            comment=comment,
            items=email_items,
            total=total
        )
        cart_items_for_payment = [{'id': str(pid), 'name': pname, 'price': pprice, 'quantity': qty} for qty, pid, pname, pprice in cart]
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({
            'ok': True,
            'order_id': order_id,
            'total': total,
            'user_email': current_user['email'],
            'user_name': name,
            'user_phone': phone,
            'cart_items': cart_items_for_payment,
        })}

    # GET ?action=orders
    if method == 'GET' and action == 'orders':
        if not current_user:
            return {'statusCode': 401, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Не авторизован'})}
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, status, total, name, phone, address, comment, created_at FROM orders WHERE user_id=%s ORDER BY created_at DESC", (current_user['id'],))
        orders = []
        for row in cur.fetchall():
            oid = row[0]
            cur2 = conn.cursor()
            cur2.execute("SELECT product_name, product_price, quantity FROM order_items WHERE order_id=%s", (oid,))
            items = [{'name': i[0], 'price': i[1], 'quantity': i[2]} for i in cur2.fetchall()]
            orders.append({'id': oid, 'status': row[1], 'total': row[2], 'name': row[3], 'phone': row[4], 'address': row[5], 'comment': row[6], 'created_at': str(row[7]), 'items': items})
        conn.close()
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'orders': orders})}

    return {'statusCode': 404, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Not found'})}