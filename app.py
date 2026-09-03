import os, sqlite3, time, hashlib, hmac, urllib.parse, json, requests, logging
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s'); log=logging.getLogger(__name__)
BASE=os.path.dirname(os.path.abspath(__file__)); DB_PATH=os.getenv('DB_PATH',os.path.join(BASE,'data.db'))
BOT_TOKEN=os.getenv('BOT_TOKEN','').strip(); ADMIN_PASSWORD=os.getenv('ADMIN_PASSWORD',''); PORT=int(os.getenv('PORT','10000')); PUBLIC_URL=os.getenv('RENDER_EXTERNAL_URL','').rstrip('/'); MINIAPP_URL=(os.getenv('MINIAPP_URL') or PUBLIC_URL).rstrip('/')
app=Flask(__name__,static_folder='miniapp')
def db(): c=sqlite3.connect(DB_PATH,timeout=20); c.row_factory=sqlite3.Row; return c
def init_db():
 c=db(); c.executescript('''CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,category TEXT,price REAL NOT NULL,old_price REAL,image_url TEXT,description TEXT,stock INTEGER NOT NULL DEFAULT 0,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL);CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_name TEXT NOT NULL,phone TEXT NOT NULL,address TEXT NOT NULL,items TEXT NOT NULL,total REAL NOT NULL,status TEXT NOT NULL DEFAULT 'Pending',created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL);CREATE TABLE IF NOT EXISTS users(telegram_id TEXT PRIMARY KEY,username TEXT,first_name TEXT,balance REAL NOT NULL DEFAULT 0,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL);CREATE TABLE IF NOT EXISTS rewards(id INTEGER PRIMARY KEY AUTOINCREMENT,telegram_id TEXT NOT NULL,amount REAL NOT NULL,event_id TEXT UNIQUE,source TEXT NOT NULL,created_at INTEGER NOT NULL);'''); c.commit(); c.close()
def admin_ok(): return bool(ADMIN_PASSWORD) and hmac.compare_digest(request.headers.get('X-Admin-Password',''),ADMIN_PASSWORD)
@app.get('/')
def home(): return send_from_directory('miniapp','index.html')
@app.get('/fashion')
def fashion(): return send_from_directory('fashion','index.html')
@app.get('/fashion/admin')
def admin(): return send_from_directory('fashion','admin.html')
@app.get('/api/products')
def products():
 c=db(); rows=c.execute('SELECT * FROM products ORDER BY id DESC').fetchall(); c.close(); return jsonify(items=[dict(r) for r in rows])
@app.post('/api/orders')
def create_order():
 b=request.get_json(silent=True) or {}; name=str(b.get('customer_name','')).strip(); phone=str(b.get('phone','')).strip(); address=str(b.get('address','')).strip(); items=b.get('items',[]); total=float(b.get('total',0))
 if not name or not phone or not address or not isinstance(items,list) or not items:return jsonify(ok=False,error='missing_order_data'),400
 now=int(time.time()); c=db(); c.execute('INSERT INTO orders(customer_name,phone,address,items,total,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',(name,phone,address,json.dumps(items,ensure_ascii=False),total,'Pending',now,now)); oid=c.lastrowid; c.commit(); c.close(); return jsonify(ok=True,order_id=oid)
@app.get('/api/admin/stats')
def stats():
 if not admin_ok(): return jsonify(error='unauthorized'),401
 c=db(); out={'products':c.execute('SELECT COUNT(*) c FROM products').fetchone()['c'],'orders':c.execute('SELECT COUNT(*) c FROM orders').fetchone()['c'],'pending':c.execute("SELECT COUNT(*) c FROM orders WHERE status='Pending'").fetchone()['c'],'sales':float(c.execute("SELECT COALESCE(SUM(total),0) s FROM orders WHERE status!='Cancelled'").fetchone()['s'])}; c.close(); return jsonify(**out)
@app.get('/api/admin/products')
def admin_products():
 if not admin_ok(): return jsonify(error='unauthorized'),401
 c=db(); rows=c.execute('SELECT * FROM products ORDER BY id DESC').fetchall(); c.close(); return jsonify(items=[dict(r) for r in rows])
@app.post('/api/admin/products')
def add_product():
 if not admin_ok(): return jsonify(error='unauthorized'),401
 b=request.get_json(silent=True) or {}; name=str(b.get('name','')).strip(); now=int(time.time())
 if not name:return jsonify(error='name_required'),400
 c=db(); c.execute('INSERT INTO products(name,category,price,old_price,image_url,description,stock,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)',(name,b.get('category',''),float(b.get('price',0)),float(b.get('old_price',0) or 0),b.get('image_url',''),b.get('description',''),int(b.get('stock',0)),now,now)); pid=c.lastrowid;c.commit();c.close();return jsonify(ok=True,id=pid)
@app.put('/api/admin/products/<int:pid>')
def edit_product(pid):
 if not admin_ok(): return jsonify(error='unauthorized'),401
 b=request.get_json(silent=True) or {}; c=db(); c.execute('UPDATE products SET name=?,category=?,price=?,old_price=?,image_url=?,description=?,stock=?,updated_at=? WHERE id=?',(str(b.get('name','')).strip(),b.get('category',''),float(b.get('price',0)),float(b.get('old_price',0) or 0),b.get('image_url',''),b.get('description',''),int(b.get('stock',0)),int(time.time()),pid));c.commit();c.close();return jsonify(ok=True)
@app.delete('/api/admin/products/<int:pid>')
def delete_product(pid):
 if not admin_ok(): return jsonify(error='unauthorized'),401
 c=db();c.execute('DELETE FROM products WHERE id=?',(pid,));c.commit();c.close();return jsonify(ok=True)
@app.get('/api/admin/orders')
def admin_orders():
 if not admin_ok(): return jsonify(error='unauthorized'),401
 c=db(); rows=c.execute('SELECT * FROM orders ORDER BY id DESC').fetchall(); c.close(); out=[]
 for r in rows:
  x=dict(r); x['items']=json.loads(x['items']); out.append(x)
 return jsonify(items=out)
@app.put('/api/admin/orders/<int:oid>')
def update_order(oid):
 if not admin_ok(): return jsonify(error='unauthorized'),401
 status=str((request.get_json(silent=True) or {}).get('status','Pending')); allowed={'Pending','Confirmed','Processing','Shipped','Delivered','Cancelled'}
 if status not in allowed:return jsonify(error='invalid_status'),400
 c=db();c.execute('UPDATE orders SET status=?,updated_at=? WHERE id=?',(status,int(time.time()),oid));c.commit();c.close();return jsonify(ok=True)
if __name__=='__main__': init_db(); app.run(host='0.0.0.0',port=PORT)