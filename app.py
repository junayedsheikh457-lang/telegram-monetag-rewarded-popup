import os, sqlite3, time, hashlib, hmac, urllib.parse
from flask import Flask, jsonify, request, send_from_directory, abort
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE, "data.db"))
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
POSTBACK_SECRET = os.getenv("POSTBACK_SECRET", "")
REWARD = float(os.getenv("REWARD_PER_AD", "0.05"))
COOLDOWN = int(os.getenv("AD_COOLDOWN_SECONDS", "30"))

app = Flask(__name__, static_folder="miniapp")

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.executescript('''
    CREATE TABLE IF NOT EXISTS users (
      telegram_id TEXT PRIMARY KEY, username TEXT, first_name TEXT,
      balance REAL NOT NULL DEFAULT 0, created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS rewards (
      id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id TEXT NOT NULL,
      amount REAL NOT NULL, event_id TEXT UNIQUE, source TEXT NOT NULL,
      created_at INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS ad_sessions (
      id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id TEXT NOT NULL,
      nonce TEXT UNIQUE NOT NULL, created_at INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS withdrawals (
      id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id TEXT NOT NULL,
      amount REAL NOT NULL, method TEXT NOT NULL, account TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'pending', created_at INTEGER NOT NULL
    );
    ''')
    con.commit(); con.close()

def tg_valid(init_data):
    if not init_data or not BOT_TOKEN: return False
    try:
        data = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        received = data.pop('hash', None)
        if not received: return False
        auth = '\n'.join(f'{k}={data[k]}' for k in sorted(data))
        secret = hmac.new(b'WebAppData', BOT_TOKEN.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret, auth.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, received): return False
        return int(time.time()) - int(data.get('auth_date','0')) < 86400
    except Exception:
        return False

def upsert_user(tid, username='', first_name=''):
    now = int(time.time()); con = db()
    con.execute('''INSERT INTO users(telegram_id,username,first_name,created_at,updated_at)
      VALUES(?,?,?,?,?) ON CONFLICT(telegram_id) DO UPDATE SET username=?,first_name=?,updated_at=?''',
      (str(tid), username or '', first_name or '', now, now, username or '', first_name or '', now))
    con.commit(); con.close()

@app.get('/')
def home(): return send_from_directory('miniapp', 'index.html')

@app.get('/api/health')
def health(): return jsonify(ok=True)

@app.post('/api/session')
def session():
    body = request.get_json(silent=True) or {}
    init_data = body.get('initData','')
    if not tg_valid(init_data): return jsonify(ok=False, error='invalid_telegram_data'), 401
    parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    user = __import__('json').loads(parsed['user'])
    tid = str(user['id']); upsert_user(tid, user.get('username',''), user.get('first_name',''))
    nonce = hashlib.sha256(f'{tid}:{time.time_ns()}'.encode()).hexdigest()
    con = db(); con.execute('INSERT INTO ad_sessions(telegram_id,nonce,created_at) VALUES(?,?,?)',(tid,nonce,int(time.time()))); con.commit(); con.close()
    return jsonify(ok=True, user_id=tid, nonce=nonce)

@app.get('/api/me')
def me():
    tid = request.args.get('user_id','')
    con=db(); row=con.execute('SELECT balance FROM users WHERE telegram_id=?',(tid,)).fetchone(); con.close()
    return jsonify(balance=float(row['balance']) if row else 0)

@app.get('/api/history')
def history():
    tid=request.args.get('user_id',''); con=db()
    rows=con.execute('SELECT amount,source,created_at FROM rewards WHERE telegram_id=? ORDER BY id DESC LIMIT 50',(tid,)).fetchall(); con.close()
    return jsonify(items=[dict(r) for r in rows])

@app.get('/api/ad-ready')
def ad_ready():
    tid=request.args.get('user_id','')
    con=db(); row=con.execute('SELECT created_at FROM ad_sessions WHERE telegram_id=? AND used=0 ORDER BY id DESC LIMIT 1',(tid,)).fetchone(); con.close()
    return jsonify(ready=bool(row and time.time()-row['created_at'] < 300))

@app.get('/monetag/postback')
def postback():
    if POSTBACK_SECRET and not hmac.compare_digest(request.args.get('secret',''), POSTBACK_SECRET): return 'forbidden',403
    tid = request.args.get('user_id') or request.args.get('ymid') or request.args.get('subid')
    event_id = request.args.get('event_id') or request.args.get('transaction_id') or request.args.get('click_id')
    if not tid: return 'missing user_id',400
    con=db();
    sess=con.execute('SELECT id FROM ad_sessions WHERE telegram_id=? AND used=0 AND created_at>=? ORDER BY id DESC LIMIT 1',(str(tid),int(time.time())-300)).fetchone()
    if not sess: con.close(); return 'no pending session',409
    if event_id and con.execute('SELECT 1 FROM rewards WHERE event_id=?',(event_id,)).fetchone(): con.close(); return 'duplicate',200
    last=con.execute('SELECT created_at FROM rewards WHERE telegram_id=? ORDER BY id DESC LIMIT 1',(str(tid),)).fetchone()
    if last and time.time()-last['created_at'] < COOLDOWN: con.close(); return 'cooldown',429
    now=int(time.time())
    con.execute('UPDATE ad_sessions SET used=1 WHERE id=?',(sess['id'],))
    con.execute('UPDATE users SET balance=balance+?,updated_at=? WHERE telegram_id=?',(REWARD,now,str(tid)))
    con.execute('INSERT INTO rewards(telegram_id,amount,event_id,source,created_at) VALUES(?,?,?,?,?)',(str(tid),REWARD,event_id or hashlib.sha256(f'{tid}:{now}:{sess["id"]}'.encode()).hexdigest(),'monetag',now))
    con.commit(); con.close(); return 'ok',200

def admin_ok(): return bool(ADMIN_PASSWORD) and hmac.compare_digest(request.headers.get('X-Admin-Password',''), ADMIN_PASSWORD)

@app.get('/admin')
def admin():
    if not admin_ok(): abort(401)
    return send_from_directory('miniapp','admin.html')

@app.get('/api/admin/stats')
def stats():
    if not admin_ok(): return jsonify(error='unauthorized'),401
    con=db(); users=con.execute('SELECT COUNT(*) c FROM users').fetchone()['c']; bal=con.execute('SELECT COALESCE(SUM(balance),0) s FROM users').fetchone()['s']; ads=con.execute('SELECT COUNT(*) c FROM rewards').fetchone()['c']; con.close()
    return jsonify(users=users,balance=float(bal),ads=ads)

@app.get('/api/admin/users')
def admin_users():
    if not admin_ok(): return jsonify(error='unauthorized'),401
    con=db(); rows=con.execute('SELECT telegram_id,username,first_name,balance,updated_at FROM users ORDER BY balance DESC LIMIT 200').fetchall(); con.close(); return jsonify(items=[dict(r) for r in rows])

@app.post('/api/admin/balance')
def admin_balance():
    if not admin_ok(): return jsonify(error='unauthorized'),401
    b=request.get_json(silent=True) or {}; tid=str(b.get('user_id','')); amount=float(b.get('amount',0));
    con=db(); con.execute('UPDATE users SET balance=balance+?,updated_at=? WHERE telegram_id=?',(amount,int(time.time()),tid)); con.commit(); con.close(); return jsonify(ok=True)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT','10000')))
