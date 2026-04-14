import json
import os
import hmac
import secrets
import time
import smtplib
import urllib.request
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import bcrypt
import psycopg2

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Auth-Token',
    'Access-Control-Max-Age': '86400',
}

BRUTE_FORCE_MAX_ATTEMPTS = 5
BRUTE_FORCE_WINDOW_SEC = 15 * 60

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
            "SELECT id, email, name, phone, address, role, token_hash, email_verified FROM users WHERE id = %s",
            (user_id,)
        )
        row = cur.fetchone()
        conn.close()
        if not row or not row[6]:
            return None
        if not hmac.compare_digest(expected_hash, row[6]):
            return None
        return {'id': row[0], 'email': row[1], 'name': row[2], 'phone': row[3], 'address': row[4], 'role': row[5], 'email_verified': row[7]}
    except Exception:
        return None

def send_verification_email(to_email: str, token: str, name: str):
    smtp_user = os.environ.get('SMTP_USER', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    if not smtp_user or not smtp_password:
        print('SMTP not configured, skipping verification email')
        return

    verify_url = f"https://{os.environ.get('SITE_HOST', 'preview--quantum-explorer-1.poehali.dev')}/verify-email?token={token}"

    html_body = f"""
    <!DOCTYPE html><html><head><meta charset="utf-8"></head>
    <body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:32px 0;">
        <tr><td align="center">
          <table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
            <tr>
              <td style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:32px 40px;text-align:center;">
                <h1 style="margin:0;color:#fff;font-size:22px;font-weight:700;">🍬 Подтвердите email</h1>
              </td>
            </tr>
            <tr>
              <td style="padding:32px 40px;">
                <p style="font-size:16px;color:#333;">Привет, <strong>{name or to_email}</strong>!</p>
                <p style="font-size:15px;color:#555;line-height:1.6;">Нажмите кнопку ниже, чтобы подтвердить ваш email и войти в магазин.</p>
                <div style="text-align:center;margin:28px 0;">
                  <a href="{verify_url}" style="background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:700;font-size:15px;display:inline-block;">
                    Подтвердить email
                  </a>
                </div>
                <p style="font-size:13px;color:#aaa;">Ссылка действительна 24 часа. Если вы не регистрировались — просто проигнорируйте это письмо.</p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body></html>
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '🍬 Подтвердите ваш email'
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())
        print(f'Verification email sent to {to_email}')
    except Exception as e:
        print(f'Failed to send verification email: {e}')

def check_brute_force(cur, ip: str, email: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) FROM login_attempts WHERE (ip = %s OR email = %s) AND attempted_at > NOW() - INTERVAL '%s seconds'",
        (ip, email, BRUTE_FORCE_WINDOW_SEC)
    )
    return cur.fetchone()[0] >= BRUTE_FORCE_MAX_ATTEMPTS

def record_failed_attempt(cur, ip: str, email: str):
    cur.execute("INSERT INTO login_attempts (ip, email) VALUES (%s, %s)", (ip, email))

def clear_attempts(cur, ip: str, email: str):
    cur.execute("DELETE FROM login_attempts WHERE ip = %s AND email = %s", (ip, email))

def handler(event: dict, context) -> dict:
    """Авторизация: регистрация с подтверждением email, вход, профиль"""
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
        cur.execute("SELECT id, email_verified FROM users WHERE email = %s", (email,))
        existing = cur.fetchone()
        if existing:
            conn.close()
            if not existing[1]:
                return {'statusCode': 409, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'EMAIL_NOT_VERIFIED', 'message': 'Email уже зарегистрирован, но не подтверждён. Проверьте почту или запросите повторное письмо.'})}
            return {'statusCode': 409, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Email уже зарегистрирован'})}
        pwd_hash = hash_password(password)
        verify_token_val = secrets.token_urlsafe(32)
        cur.execute(
            "INSERT INTO users (email, password_hash, name, email_verified, email_verify_token, email_verify_sent_at) VALUES (%s, %s, %s, FALSE, %s, NOW()) RETURNING id",
            (email, pwd_hash, name, verify_token_val)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        conn.close()
        send_verification_email(email, verify_token_val, name)
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'ok': True, 'message': 'Письмо с подтверждением отправлено на ваш email'})}

    # POST ?action=verify-email
    if method == 'POST' and action == 'verify-email':
        verify_token_val = body.get('token', '').strip()
        if not verify_token_val:
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Токен обязателен'})}
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, email, name, role FROM users WHERE email_verify_token = %s AND email_verified = FALSE AND email_verify_sent_at > NOW() - INTERVAL '24 hours'",
            (verify_token_val,)
        )
        row = cur.fetchone()
        if not row:
            conn.close()
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Ссылка недействительна или истекла'})}
        cur.execute(
            "UPDATE users SET email_verified = TRUE, email_verify_token = NULL WHERE id = %s",
            (row[0],)
        )
        token_val = generate_token(row[0], conn)
        conn.commit()
        conn.close()
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'token': token_val, 'user': {'id': row[0], 'email': row[1], 'name': row[2], 'role': row[3], 'email_verified': True}})}

    # POST ?action=resend-verification
    if method == 'POST' and action == 'resend-verification':
        email = body.get('email', '').strip().lower()
        if not email:
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Email обязателен'})}
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, email_verified FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'ok': True})}
        if row[2]:
            conn.close()
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Email уже подтверждён'})}
        new_token = secrets.token_urlsafe(32)
        cur.execute(
            "UPDATE users SET email_verify_token = %s, email_verify_sent_at = NOW() WHERE id = %s",
            (new_token, row[0])
        )
        conn.commit()
        conn.close()
        send_verification_email(email, new_token, row[1])
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'ok': True, 'message': 'Письмо отправлено повторно'})}

    # POST ?action=login
    if method == 'POST' and action == 'login':
        email = body.get('email', '').strip().lower()
        password = body.get('password', '')
        conn = get_db()
        cur = conn.cursor()
        if check_brute_force(cur, client_ip, email):
            conn.close()
            return {'statusCode': 429, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Слишком много попыток. Попробуйте через 15 минут.'})}
        cur.execute("SELECT id, email, password_hash, name, role, email_verified FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        if not row or not verify_password(password, row[2]):
            record_failed_attempt(cur, client_ip, email)
            conn.commit()
            conn.close()
            return {'statusCode': 401, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Неверный email или пароль'})}
        if not row[5]:
            conn.close()
            return {'statusCode': 403, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'EMAIL_NOT_VERIFIED', 'message': 'Подтвердите email. Проверьте почту или запросите повторное письмо.'})}
        clear_attempts(cur, client_ip, email)
        token_val = generate_token(row[0], conn)
        conn.commit()
        conn.close()
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'token': token_val, 'user': {'id': row[0], 'email': row[1], 'name': row[3], 'role': row[4], 'email_verified': True}})}

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
        cur.execute(
            "UPDATE users SET name=%s, phone=%s, address=%s WHERE id=%s",
            (name, phone, address, user['id'])
        )
        conn.commit()
        conn.close()
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'ok': True, 'user': {**user, 'name': name, 'phone': phone, 'address': address}})}

    # PUT ?action=password
    if method == 'PUT' and action == 'password':
        user = verify_token(token or '')
        if not user:
            return {'statusCode': 401, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Не авторизован'})}
        old_password = body.get('old_password', '')
        new_password = body.get('new_password', '')
        if not old_password or not new_password:
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Укажите старый и новый пароль'})}
        if len(new_password) < 6:
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Новый пароль минимум 6 символов'})}
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE id=%s", (user['id'],))
        row = cur.fetchone()
        if not row or not verify_password(old_password, row[0]):
            conn.close()
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Неверный текущий пароль'})}
        cur.execute("UPDATE users SET password_hash=%s WHERE id=%s", (hash_password(new_password), user['id']))
        conn.commit()
        conn.close()
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({'ok': True})}

    # POST ?action=yandex-oauth  — обмен code на токен и вход/регистрация
    if method == 'POST' and action == 'yandex-oauth':
        code = body.get('code', '').strip()
        if not code:
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'code обязателен'})}

        client_id = os.environ.get('YANDEX_CLIENT_ID', '')
        client_secret = os.environ.get('YANDEX_CLIENT_SECRET', '')
        if not client_id or not client_secret:
            return {'statusCode': 500, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Яндекс OAuth не настроен'})}

        # Обменяем code на access_token
        token_data = urllib.parse.urlencode({
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
        }).encode('utf-8')
        try:
            req = urllib.request.Request(
                'https://oauth.yandex.ru/token',
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                token_resp = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            return {'statusCode': 502, 'headers': CORS_HEADERS, 'body': json.dumps({'error': f'Ошибка получения токена Яндекс: {e}'})}

        ya_access_token = token_resp.get('access_token')
        if not ya_access_token:
            return {'statusCode': 502, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Яндекс не вернул access_token'})}

        # Получаем профиль пользователя
        try:
            info_req = urllib.request.Request(
                'https://login.yandex.ru/info?format=json',
                headers={'Authorization': f'OAuth {ya_access_token}'}
            )
            with urllib.request.urlopen(info_req, timeout=10) as resp:
                ya_user = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            return {'statusCode': 502, 'headers': CORS_HEADERS, 'body': json.dumps({'error': f'Ошибка получения профиля Яндекс: {e}'})}

        ya_id = str(ya_user.get('id', ''))
        ya_email = (ya_user.get('default_email') or ya_user.get('emails', [''])[0] or '').lower()
        ya_name = ya_user.get('real_name') or ya_user.get('display_name') or ya_email

        if not ya_id or not ya_email:
            return {'statusCode': 502, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Не удалось получить данные из Яндекса'})}

        conn = get_db()
        cur = conn.cursor()

        # Ищем по oauth_id
        cur.execute("SELECT id, email, name, role FROM users WHERE oauth_provider='yandex' AND oauth_id=%s", (ya_id,))
        row = cur.fetchone()

        if row:
            # Уже зарегистрирован через Яндекс — просто входим
            token_val = generate_token(row[0], conn)
            conn.commit()
            conn.close()
            return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({
                'token': token_val,
                'user': {'id': row[0], 'email': row[1], 'name': row[2], 'role': row[3], 'email_verified': True}
            })}

        # Проверяем, нет ли уже аккаунта с таким email (обычная регистрация)
        cur.execute("SELECT id, email, name, role FROM users WHERE email=%s", (ya_email,))
        existing = cur.fetchone()

        if existing:
            # Привязываем Яндекс к существующему аккаунту
            cur.execute(
                "UPDATE users SET oauth_provider='yandex', oauth_id=%s, email_verified=TRUE WHERE id=%s",
                (ya_id, existing[0])
            )
            token_val = generate_token(existing[0], conn)
            conn.commit()
            conn.close()
            return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({
                'token': token_val,
                'user': {'id': existing[0], 'email': existing[1], 'name': existing[2], 'role': existing[3], 'email_verified': True}
            })}

        # Новый пользователь — регистрируем
        cur.execute(
            "INSERT INTO users (email, password_hash, name, email_verified, oauth_provider, oauth_id) VALUES (%s, %s, %s, TRUE, 'yandex', %s) RETURNING id",
            (ya_email, '', ya_name, ya_id)
        )
        new_id = cur.fetchone()[0]
        token_val = generate_token(new_id, conn)
        conn.commit()
        conn.close()
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({
            'token': token_val,
            'user': {'id': new_id, 'email': ya_email, 'name': ya_name, 'role': 'user', 'email_verified': True}
        })}

    # POST ?action=telegram-auth — проверка данных от Telegram Login Widget
    if method == 'POST' and action == 'telegram-auth':
        tg_data = body.get('tg_data')
        if not tg_data or not isinstance(tg_data, dict):
            return {'statusCode': 400, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'tg_data обязателен'})}

        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        if not bot_token:
            return {'statusCode': 500, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Telegram бот не настроен'})}

        # Проверяем подпись от Telegram
        check_hash = tg_data.pop('hash', '')
        data_check_arr = sorted([f"{k}={v}" for k, v in tg_data.items()])
        data_check_string = '\n'.join(data_check_arr)
        secret_key = hmac.new(b'WebAppData', bot_token.encode('utf-8'), 'sha256').digest()
        computed_hash = hmac.new(secret_key, data_check_string.encode('utf-8'), 'sha256').hexdigest()

        if not hmac.compare_digest(computed_hash, check_hash):
            return {'statusCode': 403, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Неверная подпись Telegram'})}

        # Проверяем актуальность данных (не старше 1 часа)
        auth_date = int(tg_data.get('auth_date', 0))
        if int(time.time()) - auth_date > 3600:
            return {'statusCode': 403, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Данные Telegram устарели, войдите повторно'})}

        tg_id = int(tg_data.get('id', 0))
        tg_first = tg_data.get('first_name', '')
        tg_last = tg_data.get('last_name', '')
        tg_name = f"{tg_first} {tg_last}".strip() or tg_first or f"tg_{tg_id}"
        tg_username = tg_data.get('username', '')

        conn = get_db()
        cur = conn.cursor()

        # Ищем по telegram_id
        cur.execute("SELECT id, email, name, role FROM users WHERE telegram_id = %s", (tg_id,))
        row = cur.fetchone()

        if row:
            token_val = generate_token(row[0], conn)
            conn.commit()
            conn.close()
            return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({
                'token': token_val,
                'user': {'id': row[0], 'email': row[1], 'name': row[2], 'role': row[3], 'email_verified': True}
            })}

        # Новый пользователь — регистрируем без email (используем fake email на основе tg_id)
        fake_email = f"tg_{tg_id}@telegram.local"
        cur.execute("SELECT id, email, name, role FROM users WHERE email = %s", (fake_email,))
        existing = cur.fetchone()

        if existing:
            cur.execute("UPDATE users SET telegram_id = %s WHERE id = %s", (tg_id, existing[0]))
            token_val = generate_token(existing[0], conn)
            conn.commit()
            conn.close()
            return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({
                'token': token_val,
                'user': {'id': existing[0], 'email': existing[1], 'name': existing[2], 'role': existing[3], 'email_verified': True}
            })}

        cur.execute(
            "INSERT INTO users (email, password_hash, name, email_verified, telegram_id) VALUES (%s, %s, %s, TRUE, %s) RETURNING id",
            (fake_email, '', tg_name, tg_id)
        )
        new_id = cur.fetchone()[0]
        token_val = generate_token(new_id, conn)
        conn.commit()
        conn.close()

        display_name = f"@{tg_username}" if tg_username else tg_name
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': json.dumps({
            'token': token_val,
            'user': {'id': new_id, 'email': fake_email, 'name': display_name, 'role': 'user', 'email_verified': True}
        })}

    return {'statusCode': 404, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Not found'})}