import os, sqlite3, time, hashlib, hmac, urllib.parse, json, requests, logging
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log=logging.getLogger(__name__)
BASE=os.path.dirname(os.path.abspath(__file__))
DB_PATH=os.getenv('DB_PATH',os.path.join(BASE,'data.db'))
BOT_TOKEN=os.getenv('BOT_TOKEN','').strip(); ADMIN_PASSWORD=os.getenv('ADMIN_PASSWORD',''); POSTBACK_SECRET=os.getenv('POSTBACK_SECRET',''); WEBHOOK_SECRET=os.getenv('WEBHOOK_SECRET','')
REWARD=float(os.getenv('REWARD_PER_AD','0.05')); COOLDOWN=int(os.getenv('AD_COOLDOWN_SECONDS','30')); SESSION_TTL=int(os.getenv('AD_SESSION_TTL_SECONDS','300')); PORT=int(os.getenv('PORT','10000'))
PUBLIC_URL=os.getenv('RENDER_EXTERNAL_URL','').rstrip('/'); MINIAPP_URL=(os.getenv('MINIAPP_URL') or PUBLIC_URL).rstrip('/')
app=Flask(__name__,static_folder='miniapp')

def db():
 c=sqlite3.connect(DB_PATH,timeout=20); c.row_factory=sqlite3.Row; return c

def init_db():
 c=db(); c.executescript('''CREATE TABLE IF NOT EXISTS users(telegram_id TEXT PRIMARY KEY,username TEXT,first_name TEXT,balance REAL NOT NULL DEFAULT 0,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL);CREATE TABLE IF NOT EXISTS rewards(id INTEGER PRIMARY KEY AUTOINCREMENT,telegram_id TEXT NOT NULL,amount REAL NOT NULL,event_id TEXT UNIQUE,source TEXT NOT NULL,created_at INTEGER NOT NULL);CREATE TABLE IF NOT EXISTS ad_sessions(id INTEGER PRIMARY KEY AUTOINCREMENT,telegram_id TEXT NOT NULL,nonce TEXT UNIQUE NOT NULL,created_at INTEGER NOT NULL,used INTEGER NOT NULL DEFAULT 0);CREATE INDEX IF NOT EXISTS idx_sessions_nonce ON ad_sessions(nonce,used,created_at);CREATE INDEX IF NOT EXISTS idx_rewards_user ON rewards(telegram_id,created_at);'''); c.commit(); c.close()

def tg_valid(s):
 if not s or not BOT_TOKEN:return False
 try:
  d=dict(urllib.parse.parse_qsl(s,keep_blank_values=True)); received=d.pop('hash',None); auth='\n'.join(f'{k}={d[k]}' for k in sorted(d)); secret=hmac.new(b'WebAppData',BOT_TOKEN.encode(),hashlib.sha256).digest(); calc=hmac.new(secret,auth.encode(),hashlib.sha256).hexdigest(); age=int(time.time())-int(d.get('auth_date','0')); return bool(received and hmac.compare_digest(calc,received) and 0<=age<86400 and d.get('user'))
 except Exception:return False

def upsert(t,u):
 n=int(time.time()); c=db(); c.execute('''INSERT INTO users(telegram_id,username,first_name,created_at,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(telegram_id) DO UPDATE SET username=?,first_name=?,updated_at=?''',(str(t),u.get('username',''),u.get('first_name',''),n,n,u.get('username',''),u.get('first_name',''),n)); c.commit(); c.close()

def telegram(method,payload):
 if not BOT_TOKEN: log.error('BOT_TOKEN missing'); return None
 try:
  r=requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/{method}',json=payload,timeout=20); log.info('Telegram %s -> %s %s',method,r.status_code,r.text[:300]); return r
 except Exception as e: log.exception('Telegram request failed: %s',e); return None

def setup_webhook():
 if not BOT_TOKEN or not PUBLIC_URL: log.error('Cannot configure webhook: BOT_TOKEN or RENDER_EXTERNAL_URL missing'); return
 p={'url':PUBLIC_URL+'/telegram/webhook'}
 if WEBHOOK_SECRET:p['secret_token']=WEBHOOK_SECRET
 telegram('setWebhook',p)

def send_start(chat):
 if not chat:return
 p={'chat_id':chat,'text':'স্বাগতম! 🎁\n\nনিচের বাটনে ক্লিক করে Mini App ওপেন করো এবং verified rewarded ad দেখে রিওয়ার্ড নাও।'}
 if MINIAPP_URL:p['reply_markup']={'inline_keyboard':[[{'text':'🎁 অ্যাড দেখে রিওয়ার্ড নাও','web_app':{'url':MINIAPP_URL}}]]}
 telegram('sendMessage',p)

@app.get('/')
def home():return send_from_directory('miniapp','index.html')

@app.get('/api/health')
def health():return jsonify(ok=True,bot_configured=bool(BOT_TOKEN),webhook_configured=bool(PUBLIC_URL),webhook_url=(PUBLIC_URL+'/telegram/webhook') if PUBLIC_URL else None)

@app.post('/telegram/webhook')
def webhook():
 if WEBHOOK_SECRET and request.headers.get('X-Telegram-Bot-Api-Secret-Token')!=WEBHOOK_SECRET:return 'forbidden',403
 update=request.get_json(silent=True) or {}; m=update.get('message') or update.get('edited_message') or update.get('channel_post') or {}; text=str(m.get('text') or '').strip(); chat=(m.get('chat') or {}).get('id'); log.info('Telegram update received')
 if chat and text:
  cmd=text.split()[0].lower()
  if cmd=='/start' or cmd.startswith('/start@'):send_start(chat)
  elif cmd=='/help' or cmd.startswith('/help@'):telegram('sendMessage',{'chat_id':chat,'text':'🎁 Reward Bot\n\n/start — Mini App চালু করো\n/help — সাহায্য'})
 return 'ok',200

@app.post('/api/session')
def session():
 b=request.get_json(silent=True) or {}; s=b.get('initData','')
 if not tg_valid(s):return jsonify(ok=False,error='invalid_telegram_data'),401
 d=dict(urllib.parse.parse_qsl(s,keep_blank_values=True))
 try:u=json.loads(d['user']); t=str(u['id'])
 except Exception:return jsonify(ok=False,error='invalid_user_data'),401
 upsert(t,u); nonce=hashlib.sha256(f'{t}:{time.time_ns()}:{os.urandom(16).hex()}'.encode()).hexdigest(); c=db(); c.execute('INSERT INTO ad_sessions(telegram_id,nonce,created_at) VALUES(?,?,?)',(t,nonce,int(time.time()))); c.commit(); c.close(); return jsonify(ok=True,user_id=t,nonce=nonce)

@app.get('/api/me')
def me():
 t=request.args.get('user_id',''); c=db(); r=c.execute('SELECT balance FROM users WHERE telegram_id=?',(t,)).fetchone(); c.close(); return jsonify(balance=float(r['balance']) if r else 0)

@app.get('/api/history')
def history():
 t=request.args.get('user_id',''); c=db(); rows=c.execute('SELECT amount,source,created_at FROM rewards WHERE telegram_id=? ORDER BY id DESC LIMIT 50',(t,)).fetchall(); c.close(); return jsonify(items=[dict(r) for r in rows])

@app.get('/monetag/postback')
def postback():
 if POSTBACK_SECRET and not hmac.compare_digest(request.args.get('secret',''),POSTBACK_SECRET):return 'forbidden',403
 raw=request.args.get('user_id') or request.args.get('ymid') or request.args.get('subid'); event=request.args.get('event_id') or request.args.get('transaction_id') or request.args.get('click_id')
 if not raw:return 'missing user_id',400
 now=int(time.time()); c=db(); s=c.execute('SELECT id,telegram_id FROM ad_sessions WHERE nonce=? AND used=0 AND created_at>=? LIMIT 1',(str(raw),now-SESSION_TTL)).fetchone()
 if not s:s=c.execute('SELECT id,telegram_id FROM ad_sessions WHERE telegram_id=? AND used=0 AND created_at>=? ORDER BY id DESC LIMIT 1',(str(raw),now-SESSION_TTL)).fetchone()
 if not s:c.close(); return 'no pending session',409
 if event and c.execute('SELECT 1 FROM rewards WHERE event_id=?',(event,)).fetchone():c.close();return 'duplicate',200
 last=c.execute('SELECT created_at FROM rewards WHERE telegram_id=? ORDER BY id DESC LIMIT 1',(s['telegram_id'],)).fetchone()
 if last and now-last['created_at']<COOLDOWN:c.close();return 'cooldown',429
 cur=c.execute('UPDATE ad_sessions SET used=1 WHERE id=? AND used=0',(s['id'],))
 if cur.rowcount!=1:c.close();return 'already_used',409
 eid=event or hashlib.sha256(f'{s["telegram_id"]}:{now}:{s["id"]}'.encode()).hexdigest()
 try:
  c.execute('UPDATE users SET balance=balance+?,updated_at=? WHERE telegram_id=?',(REWARD,now,s['telegram_id'])); c.execute('INSERT INTO rewards(telegram_id,amount,event_id,source,created_at) VALUES(?,?,?,?,?)',(s['telegram_id'],REWARD,eid,'monetag',now)); c.commit()
 except sqlite3.IntegrityError:c.rollback();c.close();return 'duplicate',200
 c.close(); return 'ok',200

def admin_ok():return bool(ADMIN_PASSWORD) and hmac.compare_digest(request.headers.get('X-Admin-Password',''),ADMIN_PASSWORD)
@app.get('/admin')
def admin():return send_from_directory('miniapp','admin.html')
@app.get('/api/admin/stats')
def stats():
 if not admin_ok():return jsonify(error='unauthorized'),401
 c=db();o={'users':c.execute('SELECT COUNT(*) c FROM users').fetchone()['c'],'balance':float(c.execute('SELECT COALESCE(SUM(balance),0) s FROM users').fetchone()['s']),'ads':c.execute('SELECT COUNT(*) c FROM rewards').fetchone()['c']};c.close();return jsonify(**o)
@app.get('/api/admin/users')
def users():
 if not admin_ok():return jsonify(error='unauthorized'),401
 c=db();r=c.execute('SELECT telegram_id,username,first_name,balance,updated_at FROM users ORDER BY balance DESC LIMIT 200').fetchall();c.close();return jsonify(items=[dict(x) for x in r])
@app.post('/api/admin/balance')
def balance():
 if not admin_ok():return jsonify(error='unauthorized'),401
 b=request.get_json(silent=True) or {};t=str(b.get('user_id',''));a=float(b.get('amount',0));c=db();c.execute('UPDATE users SET balance=balance+?,updated_at=? WHERE telegram_id=?',(a,int(time.time()),t));c.commit();c.close();return jsonify(ok=True)

if __name__=='__main__':init_db();setup_webhook();app.run(host='0.0.0.0',port=PORT)
