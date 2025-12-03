import os
import json
import smtplib
from email.mime.text import MIMEText
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime


PORT = int(os.getenv('AUTOREPLY_PORT', '9000'))
HOST = os.getenv('AUTOREPLY_HOST', '127.0.0.1')

SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')
FROM_EMAIL = os.getenv('FROM_EMAIL', SMTP_USER or '')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', '')

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
                with open('data/subscribers.csv', 'a', encoding='utf-8') as f:
                    f.write('{ts},{name},{email},{source},{ua}\n'.format(**line))
                ok = True
                if ADMIN_EMAIL:
                    try:
                        send_email(ADMIN_EMAIL, 'New subscriber', 'Name: %s\nEmail: %s\nSource: %s' % (name, email, line['source']))
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
