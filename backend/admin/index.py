import json
import os
import hmac
import psycopg2

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Auth-Token, X-User-Id',
    'Access-Control-Max-Age': '86400',
}

def get_db():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def verify_admin(token: str):
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
            "SELECT id, email, name, role, token_hash FROM users WHERE id = %s AND role = 'admin'",
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
    """Админ панель: управление товарами, заказами, пользователями"""
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}

    method = event.get('httpMethod', 'GET')
    params = event.get('queryStringParameters') or {}
    action = params.get('action', '')
    body = {}
    if event.get('body'):
        body = json.loads(event['body'])

    token = event.get('headers', {}).get('X-Auth-Token') or event.get('headers', {}).get('x-auth-token', '')
    admin = verify_admin(token)
    if not admin:
        return {'statusCode': 403, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Доступ запрещён'})}

    # --- PRODUCTS ---
    if action == 'products':
        conn = get_db()
        cur = conn.cursor()

        if method == 'GET':
            cur.execute("SELECT id, name, description, price, emoji, image_url, button_class, in_stock FROM products ORDER BY id")
            rows = cur.fetchall()
            conn.close()
            products = [{'id': r[0], 'name': r[1], 'description': r[2], 'price': r[3], 'emoji': r[4], 'image_url': r[5], 'button_class': r[6], 'in_stock': r[7]} for r in rows]
            return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'products': products})}

        if method == 'POST':
            cur.execute("INSERT INTO products (name, description, price, emoji, image_url, button_class, in_stock) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                (body.get('name'), body.get('description'), int(body.get('price', 0)), body.get('emoji'), body.get('image_url'), body.get('button_class'), body.get('in_stock', True)))
            new_id = cur.fetchone()[0]
            conn.commit()
            conn.close()
            return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'ok': True, 'id': new_id})}

        if method == 'PUT':
            pid = body.get('id')
            cur.execute("UPDATE products SET name=%s, description=%s, price=%s, emoji=%s, image_url=%s, button_class=%s, in_stock=%s WHERE id=%s",
                (body.get('name'), body.get('description'), int(body.get('price', 0)), body.get('emoji'), body.get('image_url'), body.get('button_class'), body.get('in_stock', True), pid))
            conn.commit()
            conn.close()
            return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'ok': True})}

        if method == 'DELETE':
            pid = body.get('id') or (event.get('queryStringParameters') or {}).get('id')
            cur.execute("UPDATE products SET in_stock = FALSE WHERE id=%s", (pid,))
            conn.commit()
            conn.close()
            return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'ok': True})}

        conn.close()

    # --- ORDERS ---
    if action == 'orders':
        conn = get_db()
        cur = conn.cursor()

        if method == 'GET':
            cur.execute("SELECT o.id, o.status, o.total, o.name, o.phone, o.address, o.comment, o.created_at, u.email FROM orders o LEFT JOIN users u ON o.user_id = u.id ORDER BY o.created_at DESC")
            orders = []
            for row in cur.fetchall():
                oid = row[0]
                cur2 = conn.cursor()
                cur2.execute("SELECT product_name, product_price, quantity FROM order_items WHERE order_id=%s", (oid,))
                items = [{'name': i[0], 'price': i[1], 'quantity': i[2]} for i in cur2.fetchall()]
                orders.append({'id': oid, 'status': row[1], 'total': row[2], 'name': row[3], 'phone': row[4], 'address': row[5], 'comment': row[6], 'created_at': str(row[7]), 'user_email': row[8], 'items': items})
            conn.close()
            return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'orders': orders})}

        if method == 'PUT':
            oid = body.get('id')
            status = body.get('status')
            cur.execute("UPDATE orders SET status=%s WHERE id=%s", (status, oid))
            conn.commit()
            conn.close()
            return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'ok': True})}

        conn.close()

    # --- USERS ---
    if action == 'users':
        conn = get_db()
        cur = conn.cursor()

        if method == 'GET':
            cur.execute("SELECT id, email, name, phone, role, created_at FROM users ORDER BY created_at DESC")
            rows = cur.fetchall()
            conn.close()
            users = [{'id': r[0], 'email': r[1], 'name': r[2], 'phone': r[3], 'role': r[4], 'created_at': str(r[5])} for r in rows]
            return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'users': users})}

        if method == 'PUT':
            uid = body.get('id')
            role = body.get('role')
            cur.execute("UPDATE users SET role=%s WHERE id=%s", (role, uid))
            conn.commit()
            conn.close()
            return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'ok': True})}

        conn.close()

    # --- STATS ---
    if method == 'GET' and action == 'stats':
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM orders")
        orders_count = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(total), 0) FROM orders")
        revenue = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE role='user'")
        users_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM products WHERE in_stock=TRUE")
        products_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM orders WHERE status='new'")
        new_orders = cur.fetchone()[0]
        conn.close()
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'orders_count': orders_count, 'revenue': revenue, 'users_count': users_count, 'products_count': products_count, 'new_orders': new_orders})}

    return {'statusCode': 404, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Not found'})}