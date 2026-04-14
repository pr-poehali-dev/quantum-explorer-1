import json
import os
import hmac
import secrets
import time
import smtplib
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

    return {'statusCode': 404, 'headers': CORS_HEADERS, 'body': json.dumps({'error': 'Not found'})}
