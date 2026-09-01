import os,sqlite3,time,hashlib,hmac,urllib.parse,json,requests
from flask import Flask,jsonify,request,send_from_directory
from dotenv import load_dotenv
load_dotenv()
BASE=os.path.dirname(os.path.abspath(__file__));DB_PATH=os.getenv('DB_PATH',os.path.join(BASE,'data.db'));BOT_TOKEN=os.getenv('BOT_TOKEN','');ADMIN_PASSWORD=os.getenv('ADMIN_PASSWORD','');POSTBACK_SECRET=os.getenv('POSTBACK_SECRET','');WEBHOOK_SECRET=os.getenv('WEBHOOK_SECRET','');REWARD=float(os.getenv('REWARD_PER_AD','0.05'));COOLDOWN=int(os.getenv('AD_COOLDOWN_SECONDS','30'));PORT=int(os.getenv('PORT','10000'));PUBLIC_URL=os.getenv('RENDER_EXTERNAL_URL','').rstrip('/');MINIAPP_URL=os.getenv('MINIAPP_URL') or PUBLIC_URL
app=Flask(__name__,static_folder='miniapp')
def db():
 c=sqlite3.connect(DB_PATH);c.row_factory=sqlite3.Row;return c
def init_db():
 c=db();c.executescript('''CREATE TABLE IF NOT EXISTS users(telegram_id TEXT PRIMARY KEY,username TEXT,first_name TEXT,balance REAL NOT NULL DEFAULT 0,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL);CREATE TABLE IF NOT EXISTS rewards(id INTEGER PRIMARY KEY AUTOINCREMENT,telegram_id TEXT NOT NULL,amount REAL NOT NULL,event_id TEXT UNIQUE,source TEXT NOT NULL,created_at INTEGER NOT NULL);CREATE TABLE IF NOT EXISTS ad_sessions(id INTEGER PRIMARY KEY AUTOINCREMENT,telegram_id TEXT NOT NULL,nonce TEXT UNIQUE NOT NULL,created_at INTEGER NOT NULL,used INTEGER NOT NULL DEFAULT 0);''');c.commit();c.close()
def tg_valid(s):
 if not s or not BOT_TOKEN:return False
 try:
  d=dict(urllib.parse.parse_qsl(s,keep_blank_values=True));received=d.pop('hash',None);auth='\n'.join(f'{k}={d[k]}' for k in sorted(d));secret=hmac.new(b'WebAppData',BOT_TOKEN.encode(),hashlib.sha256).digest();calc=hmac.new(secret,auth.encode(),hashlib.sha256).hexdigest();return bool(received and hmac.compare_digest(calc,received) and int(time.time())-int(d.get('auth_date','0'))<86400)
 except:return False
def upsert(t,u):
 n=int(time.time());c=db();c.execute('''INSERT INTO users(telegram_id,username,first_name,created_at,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(telegram_id) DO UPDATE SET username=?,first_name=?,updated_at=?''',(str(t),u.get('username',''),u.get('first_name',''),n,n,u.get('username',''),u.get('first_name',''),n));c.commit();c.close()
def telegram(method,payload):return requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/{method}',json=payload,timeout=20)
def setup_webhook():
 if BOT_TOKEN and PUBLIC_URL:
  p={'url':PUBLIC_URL+'/telegram/webhook'}
  if WEBHOOK_SECRET:p['secret_token']=WEBHOOK_SECRET
  print('setWebhook:',telegram('setWebhook',p).text)
def send_start(chat):telegram('sendMessage',{'chat_id':chat,'text':'স্বাগতম!\n\nনিচের বাটনে ক্লিক করে Mini App ওপেন করো এবং verified rewarded ad দেখে রিওয়ার্ড নাও।','reply_markup':{'inline_keyboard':[[{'text':'🎁 অ্যাড দেখে রিওয়ার্ড নাও','web_app':{'url':MINIAPP_URL}}]]}})
@app.get('/')
def home():return send_from_directory('miniapp','index.html')
@app.get('/api/health')
def health():return jsonify(ok=True)
@app.post('/telegram/webhook')
def webhook():
 if WEBHOOK_SECRET and request.headers.get('X-Telegram-Bot-Api-Secret-Token')!=WEBHOOK_SECRET:return 'forbidden',403
 m=(request.get_json(silent=True) or {}).get('message') or {}
 if str(m.get('text','')).startswith('/start'):send_start(m.get('chat',{}).get('id'))
 return 'ok'
@app.post('/api/session')
def session():
 b=request.get_json(silent=True) or {};s=b.get('initData','')
 if not tg_valid(s):return jsonify(ok=False,error='invalid_telegram_data'),401
 d=dict(urllib.parse.parse_qsl(s,keep_blank_values=True));u=json.loads(d['user']);t=str(u['id']);upsert(t,u);nonce=hashlib.sha256(f'{t}:{time.time_ns()}'.encode()).hexdigest();c=db();c.execute('INSERT INTO ad_sessions(telegram_id,nonce,created_at) VALUES(?,?,?)',(t,nonce,int(time.time())));c.commit();c.close();return jsonify(ok=True,user_id=t,nonce=nonce)
@app.get('/api/me')
def me():
 t=request.args.get('user_id','');c=db();r=c.execute('SELECT balance FROM users WHERE telegram_id=?',(t,)).fetchone();c.close();return jsonify(balance=float(r['balance']) if r else 0)
@app.get('/api/history')
def history():
 t=request.args.get('user_id','');c=db();rows=c.execute('SELECT amount,source,created_at FROM rewards WHERE telegram_id=? ORDER BY id DESC LIMIT 50',(t,)).fetchall();c.close();return jsonify(items=[dict(r) for r in rows])
@app.get('/monetag/postback')
def postback():
 if POSTBACK_SECRET and not hmac.compare_digest(request.args.get('secret',''),POSTBACK_SECRET):return 'forbidden',403
 t=request.args.get('user_id') or request.args.get('ymid') or request.args.get('subid');event=request.args.get('event_id') or request.args.get('transaction_id') or request.args.get('click_id')
 if not t:return 'missing user_id',400
 c=db();s=c.execute('SELECT id FROM ad_sessions WHERE telegram_id=? AND used=0 AND created_at>=? ORDER BY id DESC LIMIT 1',(str(t),int(time.time())-300)).fetchone()
 if not s:c.close();return 'no pending session',409
 if event and c.execute('SELECT 1 FROM rewards WHERE event_id=?',(event,)).fetchone():c.close();return 'duplicate',200
 last=c.execute('SELECT created_at FROM rewards WHERE telegram_id=? ORDER BY id DESC LIMIT 1',(str(t),)).fetchone()
 if last and time.time()-last['created_at']<COOLDOWN:c.close();return 'cooldown',429
 now=int(time.time());c.execute('UPDATE ad_sessions SET used=1 WHERE id=?',(s['id'],));c.execute('UPDATE users SET balance=balance+?,updated_at=? WHERE telegram_id=?',(REWARD,now,str(t)));eid=event or hashlib.sha256(f'{t}:{now}:{s["id"]}'.encode()).hexdigest();c.execute('INSERT INTO rewards(telegram_id,amount,event_id,source,created_at) VALUES(?,?,?,?,?)',(str(t),REWARD,eid,'monetag',now));c.commit();c.close();return 'ok',200
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
