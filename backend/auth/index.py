import json
import os
import hashlib
import hmac
import secrets
import time
import psycopg2

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Auth-Token, X-User-Id',
    'Access-Control-Max-Age': '86400',
}

def get_db():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def hash_password(password: str) -> str:
    salt = os.environ.get('SECRET_KEY', 'default_salt_change_me')
    return hashlib.sha256((salt + password).encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_password(password), hashed)

def generate_token(user_id: int) -> str:
    salt = os.environ.get('SECRET_KEY', 'default_salt_change_me')
    payload = f"{user_id}:{int(time.time())}:{secrets.token_hex(16)}"
    token = hashlib.sha256((salt + payload).encode()).hexdigest()
    return f"{user_id}:{token}"

def verify_token(token: str):
    try:
        user_id_str, _ = token.split(':', 1)
        user_id = int(user_id_str)
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, email, name, phone, address, role FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return {'id': row[0], 'email': row[1], 'name': row[2], 'phone': row[3], 'address': row[4], 'role': row[5]}
    except Exception:
        return None

def handler(event: dict, context) -> dict:
    """Авторизация: регистрация, вход, профиль, обновление данных"""
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}

    method = event.get('httpMethod', 'GET')
    params = event.get('queryStringParameters') or {}
    action = params.get('action', '')
    body = {}
    if event.get('body'):
        body = json.loads(event['body'])

    token = event.get('headers', {}).get('X-Auth-Token') or event.get('headers', {}).get('x-auth-token', '')

    # POST ?action=register
    if method == 'POST' and action == 'register':
        email = body.get('email', '').strip().lower()
        password = body.get('password', '')
        name = body.get('name', '').strip()
        if not email or not password:
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Email и пароль обязательны'})}
        if len(password) < 6:
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Пароль минимум 6 символов'})}
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            conn.close()
            return {'statusCode': 409, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Email уже зарегистрирован'})}
        pwd_hash = hash_password(password)
        cur.execute("INSERT INTO users (email, password_hash, name) VALUES (%s, %s, %s) RETURNING id", (email, pwd_hash, name))
        user_id = cur.fetchone()[0]
        conn.commit()
        conn.close()
        token_val = generate_token(user_id)
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'token': token_val, 'user': {'id': user_id, 'email': email, 'name': name, 'role': 'user'}})}

    # POST ?action=login
    if method == 'POST' and action == 'login':
        email = body.get('email', '').strip().lower()
        password = body.get('password', '')
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, email, password_hash, name, role FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        conn.close()
        if not row or not verify_password(password, row[2]):
            return {'statusCode': 401, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Неверный email или пароль'})}
        token_val = generate_token(row[0])
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'token': token_val, 'user': {'id': row[0], 'email': row[1], 'name': row[3], 'role': row[4]}})}

    # GET ?action=me
    if method == 'GET' and action == 'me':
        user = verify_token(token or '')
        if not user:
            return {'statusCode': 401, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Не авторизован'})}
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'user': user})}

    # PUT ?action=profile
    if method == 'PUT' and action == 'profile':
        user = verify_token(token or '')
        if not user:
            return {'statusCode': 401, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Не авторизован'})}
        name = body.get('name', user['name'])
        phone = body.get('phone', user['phone'])
        address = body.get('address', user['address'])
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET name=%s, phone=%s, address=%s WHERE id=%s", (name, phone, address, user['id']))
        conn.commit()
        conn.close()
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'ok': True})}

    # PUT ?action=password
    if method == 'PUT' and action == 'password':
        user = verify_token(token or '')
        if not user:
            return {'statusCode': 401, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Не авторизован'})}
        old_password = body.get('old_password', '')
        new_password = body.get('new_password', '')
        if len(new_password) < 6:
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Пароль минимум 6 символов'})}
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE id=%s", (user['id'],))
        row = cur.fetchone()
        if not row or not verify_password(old_password, row[0]):
            conn.close()
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Старый пароль неверен'})}
        cur.execute("UPDATE users SET password_hash=%s WHERE id=%s", (hash_password(new_password), user['id']))
        conn.commit()
        conn.close()
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'ok': True})}

    return {'statusCode': 404, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Not found'})}