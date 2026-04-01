import json
import os
import hmac
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import psycopg2

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Auth-Token, X-User-Id',
    'Access-Control-Max-Age': '86400',
}

def get_db():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def send_order_email(to_email: str, order_id: int, name: str, address: str, phone: str, items: list, total: float):
    smtp_host = os.environ.get('SMTP_HOST', '')
    smtp_port = int(os.environ.get('SMTP_PORT', 465))
    smtp_user = os.environ.get('SMTP_USER', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')

    if not smtp_host or not smtp_user or not smtp_password:
        return  # SMTP не настроен — пропускаем

    items_rows = ''.join(
        f"<tr><td style='padding:6px 12px;border-bottom:1px solid #f0f0f0'>{i['name']}</td>"
        f"<td style='padding:6px 12px;border-bottom:1px solid #f0f0f0;text-align:center'>{i['quantity']}</td>"
        f"<td style='padding:6px 12px;border-bottom:1px solid #f0f0f0;text-align:right'>{int(i['price'] * i['quantity']):,} ₽</td></tr>"
        for i in items
    )

    html = f"""
    <html><body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif">
    <div style="max-width:560px;margin:32px auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08)">
      <div style="background:#18181b;padding:28px 32px">
        <h1 style="margin:0;color:#fff;font-size:22px;letter-spacing:-0.5px">Заказ #{ order_id } оформлен ✅</h1>
      </div>
      <div style="padding:28px 32px">
        <p style="margin:0 0 8px;color:#444">Привет, <strong>{ name }</strong>!</p>
        <p style="margin:0 0 24px;color:#666;font-size:14px">Ваш заказ успешно принят. Мы свяжемся с вами по номеру <strong>{ phone }</strong>.</p>

        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin-bottom:20px">
          <thead>
            <tr style="background:#f5f5f5">
              <th style="padding:8px 12px;text-align:left;font-size:13px;color:#888;font-weight:600">Товар</th>
              <th style="padding:8px 12px;text-align:center;font-size:13px;color:#888;font-weight:600">Кол-во</th>
              <th style="padding:8px 12px;text-align:right;font-size:13px;color:#888;font-weight:600">Сумма</th>
            </tr>
          </thead>
          <tbody>{ items_rows }</tbody>
        </table>

        <div style="background:#f9f9f9;border-radius:10px;padding:14px 16px;display:flex;justify-content:space-between;margin-bottom:20px">
          <span style="font-size:15px;color:#444;font-weight:600">Итого:</span>
          <span style="font-size:17px;color:#18181b;font-weight:700">{ int(total):,} ₽</span>
        </div>

        <p style="margin:0 0 4px;font-size:13px;color:#888">Адрес доставки</p>
        <p style="margin:0 0 20px;font-size:14px;color:#333">{ address }</p>

        <p style="margin:0;font-size:13px;color:#aaa;text-align:center">Это автоматическое письмо — отвечать на него не нужно</p>
      </div>
    </div>
    </body></html>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'Заказ #{order_id} оформлен'
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg.attach(MIMEText(html, 'html', 'utf-8'))

    try:
        context = ssl.create_default_context()
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, to_email, msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, to_email, msg.as_string())
    except Exception as e:
        print(f'[email] Ошибка отправки письма: {e}')

def verify_token(token: str):
    if not token:
        return None
    try:
        parts = token.split(':', 1)
        if len(parts) != 2:
            return None
        user_id_str, token_sig = parts
        user_id = int(user_id_str)

        expected_hash = hmac.new(
            os.environ['SECRET_KEY'].encode('utf-8'),
            token_sig.encode('utf-8'),
            'sha256'
        ).hexdigest()

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, email, name, role, token_hash FROM users WHERE id = %s",
            (user_id,)
        )
        row = cur.fetchone()
        conn.close()

        if not row or not row[4]:
            return None
        if not hmac.compare_digest(expected_hash, row[4]):
            return None

        return {'id': row[0], 'email': row[1], 'name': row[2], 'role': row[3]}
    except Exception:
        return None

def handler(event: dict, context) -> dict:
    """Магазин: товары, корзина, заказы"""
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}

    method = event.get('httpMethod', 'GET')
    params = event.get('queryStringParameters') or {}
    action = params.get('action', '')
    body = {}
    if event.get('body'):
        body = json.loads(event['body'])

    token = event.get('headers', {}).get('X-Auth-Token') or event.get('headers', {}).get('x-auth-token', '')

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
        user = verify_token(token)
        if not user:
            return {'statusCode': 401, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Не авторизован'})}
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT ci.id, ci.quantity, p.id, p.name, p.price, p.emoji, p.image_url
            FROM cart_items ci JOIN products p ON ci.product_id = p.id
            WHERE ci.user_id = %s
        """, (user['id'],))
        rows = cur.fetchall()
        conn.close()
        items = [{'cart_id': r[0], 'quantity': r[1], 'product_id': r[2], 'name': r[3], 'price': r[4], 'emoji': r[5], 'image_url': r[6]} for r in rows]
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'items': items})}

    # POST ?action=cart
    if method == 'POST' and action == 'cart':
        user = verify_token(token)
        if not user:
            return {'statusCode': 401, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Не авторизован'})}
        product_id = body.get('product_id')
        quantity = int(body.get('quantity', 1))
        if not product_id:
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'product_id обязателен'})}
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO cart_items (user_id, product_id, quantity)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, product_id)
            DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity
        """, (user['id'], product_id, quantity))
        conn.commit()
        conn.close()
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'ok': True})}

    # PUT ?action=cart
    if method == 'PUT' and action == 'cart':
        user = verify_token(token)
        if not user:
            return {'statusCode': 401, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Не авторизован'})}
        product_id = body.get('product_id')
        quantity = int(body.get('quantity', 1))
        conn = get_db()
        cur = conn.cursor()
        if quantity <= 0:
            cur.execute("DELETE FROM cart_items WHERE user_id=%s AND product_id=%s", (user['id'], product_id))
        else:
            cur.execute("UPDATE cart_items SET quantity=%s WHERE user_id=%s AND product_id=%s", (quantity, user['id'], product_id))
        conn.commit()
        conn.close()
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'ok': True})}

    # POST ?action=orders
    if method == 'POST' and action == 'orders':
        user = verify_token(token)
        if not user:
            return {'statusCode': 401, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Не авторизован'})}
        name = body.get('name', user.get('name', ''))
        phone = body.get('phone', '')
        address = body.get('address', '')
        comment = body.get('comment', '')
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT ci.quantity, p.id, p.name, p.price
            FROM cart_items ci JOIN products p ON ci.product_id = p.id
            WHERE ci.user_id = %s
        """, (user['id'],))
        cart = cur.fetchall()
        if not cart:
            conn.close()
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Корзина пуста'})}
        total = sum(r[0] * r[3] for r in cart)
        cur.execute("INSERT INTO orders (user_id, total, name, phone, address, comment) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                    (user['id'], total, name, phone, address, comment))
        order_id = cur.fetchone()[0]
        for qty, pid, pname, pprice in cart:
            cur.execute("INSERT INTO order_items (order_id, product_id, product_name, product_price, quantity) VALUES (%s, %s, %s, %s, %s)",
                        (order_id, pid, pname, pprice, qty))
        cur.execute("DELETE FROM cart_items WHERE user_id=%s", (user['id'],))
        conn.commit()
        conn.close()

        # Отправляем письмо клиенту
        email_items = [{'name': pname, 'price': pprice, 'quantity': qty} for qty, pid, pname, pprice in cart]
        send_order_email(
            to_email=user['email'],
            order_id=order_id,
            name=name,
            address=address,
            phone=phone,
            items=email_items,
            total=total
        )

        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'ok': True, 'order_id': order_id})}

    # GET ?action=orders
    if method == 'GET' and action == 'orders':
        user = verify_token(token)
        if not user:
            return {'statusCode': 401, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Не авторизован'})}
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, status, total, name, phone, address, comment, created_at FROM orders WHERE user_id=%s ORDER BY created_at DESC", (user['id'],))
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