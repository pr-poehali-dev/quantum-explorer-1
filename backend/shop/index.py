import json
import os
import hashlib
import psycopg2

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Auth-Token, X-User-Id',
    'Access-Control-Max-Age': '86400',
}

def get_db():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def verify_token(token: str):
    if not token:
        return None
    try:
        user_id_str, _ = token.split(':', 1)
        user_id = int(user_id_str)
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, email, name, role FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
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