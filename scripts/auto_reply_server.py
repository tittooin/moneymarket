import os
import json
import smtplib
from email.mime.text import MIMEText
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import subprocess
import hashlib


PORT = int(os.getenv('AUTOREPLY_PORT', '9000'))
HOST = os.getenv('AUTOREPLY_HOST', '127.0.0.1')

SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')
FROM_EMAIL = os.getenv('FROM_EMAIL', SMTP_USER or '')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', '')
SUBSCRIBE_GIT_SYNC = os.getenv('SUBSCRIBE_GIT_SYNC', '')
GIT_REMOTE = os.getenv('GIT_REMOTE', 'origin')
GIT_BRANCH = os.getenv('GIT_BRANCH', 'main')
REPO_PATH = os.getenv('REPO_PATH', '')
STORE_RAW = os.getenv('SUBSCRIBE_STORE_RAW', '1')

def mask_email(email: str) -> str:
    try:
        local, domain = email.split('@', 1)
        dl = domain.split('.')
        d0 = dl[0]
        masked_local = (local[:2] + '***') if len(local) >= 2 else (local[:1] + '***')
        masked_domain = (d0[:3] + '***') if len(d0) >= 3 else (d0[:1] + '***')
        suffix = '.' + '.'.join(dl[1:]) if len(dl) > 1 else ''
        return masked_local + '@' + masked_domain + suffix
    except Exception:
        return '***@***'

def email_fingerprint(email: str) -> str:
    return hashlib.sha256(email.encode('utf-8')).hexdigest()[:10]

def send_email(to_email, subject, body):
    if not SMTP_HOST or not FROM_EMAIL:
        return True
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email
    s = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    s.starttls()
    if SMTP_USER and SMTP_PASS:
        s.login(SMTP_USER, SMTP_PASS)
    s.sendmail(FROM_EMAIL, [to_email] + ([ADMIN_EMAIL] if ADMIN_EMAIL else []), msg.as_string())
    s.quit()
    return True

class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()
    def do_POST(self):
        if self.path not in ('/api/auto-reply','/api/subscribe'):
            self.send_response(404)
            self._cors()
            self.end_headers()
            return
        length = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(length).decode('utf-8') if length > 0 else '{}'
        try:
            data = json.loads(raw)
        except Exception:
            data = {}
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip()
        subject = (data.get('subject') or 'Thank you').strip()
        body = (data.get('body') or '').strip()
        if not email or '@' not in email:
            self.send_response(400)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': False, 'error': 'invalid_email'}).encode('utf-8'))
            return
        ok = False
        if self.path == '/api/auto-reply':
            try:
                ok = send_email(email, subject, body)
            except Exception:
                ok = False
        else:
            try:
                os.makedirs('data', exist_ok=True)
                line = {
                    'ts': datetime.utcnow().isoformat(),
                    'name': name,
                    'email': email,
                    'source': (data.get('source') or ''),
                    'ua': (data.get('ua') or '')
                }
                os.makedirs('data', exist_ok=True)
                masked = {
                    'ts': line['ts'],
                    'name': name,
                    'email_masked': mask_email(email),
                    'fingerprint': email_fingerprint(email),
                    'source': line['source'],
                    'ua': line['ua']
                }
                # write raw (local-only)
                try:
                    if STORE_RAW == '1':
                        with open('data/subscribers.raw.csv', 'a', encoding='utf-8') as fraw:
                            fraw.write('{ts},{name},{email},{source},{ua}\n'.format(**line))
                except Exception:
                    pass
                # write masked (safe to commit)
                with open('data/subscribers.masked.csv', 'a', encoding='utf-8') as fm:
                    fm.write('{ts},{name},{email_masked},{fingerprint},{source},{ua}\n'.format(**masked))
                ok = True
                if ADMIN_EMAIL:
                    try:
                        send_email(ADMIN_EMAIL, 'New subscriber', 'Name: %s\nEmail: %s\nSource: %s' % (name, email, line['source']))
                    except Exception:
                        pass
                if SUBSCRIBE_GIT_SYNC:
                    try:
                        cwd = REPO_PATH or os.getcwd()
                        subprocess.run(['git','add','data/subscribers.masked.csv'], cwd=cwd, check=False)
                        msg = 'chore(subscribers): +1 %s' % (masked['fingerprint'])
                        subprocess.run(['git','commit','-m', msg], cwd=cwd, check=False)
                        subprocess.run(['git','pull','--rebase',GIT_REMOTE,GIT_BRANCH], cwd=cwd, check=False)
                        subprocess.run(['git','push',GIT_REMOTE,GIT_BRANCH], cwd=cwd, check=False)
                    except Exception:
                        pass
            except Exception:
                ok = False
        code = 200 if ok else 500
        self.send_response(code)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'ok': ok}).encode('utf-8'))

def run():
    srv = HTTPServer((HOST, PORT), Handler)
    srv.serve_forever()

if __name__ == '__main__':
    run()
