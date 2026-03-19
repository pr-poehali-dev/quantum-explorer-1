import json
import os
import hmac
import secrets
import time
import bcrypt
import psycopg2

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Auth-Token, X-User-Id',
    'Access-Control-Max-Age': '86400',
}

BRUTE_FORCE_MAX_ATTEMPTS = 5
BRUTE_FORCE_WINDOW_SEC = 15 * 60  # 15 минут

def get_db():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def generate_token(user_id: int, conn) -> str:
    """Генерирует токен и сохраняет его хеш в БД"""
    nonce = secrets.token_hex(32)
    token_sig = f"{user_id}:{int(time.time())}:{nonce}"
    token = f"{user_id}:{token_sig}"
    token_hash = hmac.new(
        os.environ['SECRET_KEY'].encode('utf-8'),
        token_sig.encode('utf-8'),
        'sha256'
    ).hexdigest()
    cur = conn.cursor()
    cur.execute("UPDATE users SET token_hash = %s WHERE id = %s", (token_hash, user_id))
    return token

def verify_token(token: str):
    """Проверяет токен: извлекает user_id и сверяет подпись с БД"""
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
            "SELECT id, email, name, phone, address, role, token_hash FROM users WHERE id = %s",
            (user_id,)
        )
        row = cur.fetchone()
        conn.close()

        if not row or not row[6]:
            return None
        if not hmac.compare_digest(expected_hash, row[6]):
            return None

        return {'id': row[0], 'email': row[1], 'name': row[2], 'phone': row[3], 'address': row[4], 'role': row[5]}
    except Exception:
        return None

def check_brute_force(cur, ip: str, email: str) -> bool:
    """Возвращает True если лимит попыток превышен"""
    cur.execute(
        "SELECT COUNT(*) FROM login_attempts WHERE (ip = %s OR email = %s) AND attempted_at > NOW() - INTERVAL '%s seconds'",
        (ip, email, BRUTE_FORCE_WINDOW_SEC)
    )
    count = cur.fetchone()[0]
    return count >= BRUTE_FORCE_MAX_ATTEMPTS

def record_failed_attempt(cur, ip: str, email: str):
    """Записывает неудачную попытку входа"""
    cur.execute(
        "INSERT INTO login_attempts (ip, email) VALUES (%s, %s)",
        (ip, email)
    )

def clear_attempts(cur, ip: str, email: str):
    """Очищает попытки после успешного входа"""
    cur.execute(
        "DELETE FROM login_attempts WHERE ip = %s AND email = %s",
        (ip, email)
    )

def handler(event: dict, context) -> dict:
    """Авторизация: регистрация, вход, профиль, обновление данных. Защита от брутфорса: блокировка на 15 мин после 5 неудачных попыток."""
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}

    method = event.get('httpMethod', 'GET')
    params = event.get('queryStringParameters') or {}
    action = params.get('action', '')
    body = {}
    if event.get('body'):
        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError:
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Некорректный JSON'})}

    token = event.get('headers', {}).get('X-Auth-Token') or event.get('headers', {}).get('x-auth-token', '')
    client_ip = (event.get('requestContext') or {}).get('identity', {}).get('sourceIp', 'unknown')

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
        token_val = generate_token(user_id, conn)
        conn.commit()
        conn.close()
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'token': token_val, 'user': {'id': user_id, 'email': email, 'name': name, 'role': 'user'}})}

    # POST ?action=login
    if method == 'POST' and action == 'login':
        email = body.get('email', '').strip().lower()
        password = body.get('password', '')

        conn = get_db()
        cur = conn.cursor()

        if check_brute_force(cur, client_ip, email):
            conn.close()
            return {'statusCode': 429, 'headers': CORS_HEADERS, 'body': json.dumps({
                'error': 'Слишком много попыток входа. Попробуйте через 15 минут.'
            })}

        cur.execute("SELECT id, email, password_hash, name, role FROM users WHERE email = %s", (email,))
        row = cur.fetchone()

        if not row or not verify_password(password, row[2]):
            record_failed_attempt(cur, client_ip, email)
            conn.commit()
            conn.close()
            return {'statusCode': 401, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Неверный email или пароль'})}

        clear_attempts(cur, client_ip, email)
        token_val = generate_token(row[0], conn)
        conn.commit()
        conn.close()
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
