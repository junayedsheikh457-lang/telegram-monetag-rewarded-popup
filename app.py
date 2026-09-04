import os, sqlite3, time, hashlib, hmac, urllib.parse, json, requests, logging
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s'); log=logging.getLogger(__name__)
BASE=os.path.dirname(os.path.abspath(__file__)); DB_PATH=os.getenv('DB_PATH',os.path.join(BASE,'data.db'))
BOT_TOKEN=os.getenv('BOT_TOKEN','').strip(); ADMIN_PASSWORD=os.getenv('ADMIN_PASSWORD',''); PORT=int(os.getenv('PORT','10000')); PUBLIC_URL=os.getenv('RENDER_EXTERNAL_URL','').rstrip('/'); MINIAPP_URL=(os.getenv('MINIAPP_URL') or PUBLIC_URL).rstrip('/')
app=Flask(__name__,static_folder='miniapp')
@app.after_request
def cors(response):
 response.headers['Access-Control-Allow-Origin']='*'
 response.headers['Access-Control-Allow-Headers']='Content-Type, X-Admin-Password'
 response.headers['Access-Control-Allow-Methods']='GET,POST,PUT,DELETE,OPTIONS'
 return response
def db():
 c=sqlite3.connect(DB_PATH,timeout=60)
 c.row_factory=sqlite3.Row
 c.execute('PRAGMA busy_timeout=60000')
 try: c.execute('PRAGMA journal_mode=WAL')
 except sqlite3.OperationalError: pass
 c.execute('PRAGMA synchronous=NORMAL')
 return c
def init_db():
 c=db()
 c.executescript('''CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,category TEXT,price REAL NOT NULL,old_price REAL,image_url TEXT,description TEXT,stock INTEGER NOT NULL DEFAULT 0,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL);CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_name TEXT NOT NULL,phone TEXT NOT NULL,address TEXT NOT NULL,items TEXT NOT NULL,total REAL NOT NULL,status TEXT NOT NULL DEFAULT 'Pending',created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL);CREATE TABLE IF NOT EXISTS users(telegram_id TEXT PRIMARY KEY,username TEXT,first_name TEXT,balance REAL NOT NULL DEFAULT 0,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL);CREATE TABLE IF NOT EXISTS rewards(id INTEGER PRIMARY KEY AUTOINCREMENT,telegram_id TEXT NOT NULL,amount REAL NOT NULL,event_id TEXT UNIQUE,source TEXT NOT NULL,created_at INTEGER NOT NULL);''')
 try: c.execute("ALTER TABLE products ADD COLUMN gallery TEXT DEFAULT '[]'")
 except sqlite3.OperationalError: pass
 c.commit(); c.close()
def admin_ok(): return bool(ADMIN_PASSWORD) and hmac.compare_digest(request.headers.get('X-Admin-Password',''),ADMIN_PASSWORD)
def product_dict(r):
 x=dict(r); x['image']=x.get('image_url') or ''; x['gallery']=json.loads(x.get('gallery') or '[]')
 if x['image'] and (not x['gallery'] or x['gallery'][0]!=x['image']): x['gallery']=[x['image']]+[u for u in x['gallery'] if u!=x['image']]
 return x
@app.get('/')
def home(): return send_from_directory('miniapp','index.html')
@app.get('/fashion')
def fashion(): return send_from_directory('fashion','index.html')
@app.get('/fashion/admin')
def admin(): return send_from_directory('fashion','admin.html')
@app.get('/api/products')
def products():
 c=db(); rows=c.execute('SELECT * FROM products ORDER BY id DESC').fetchall(); c.close(); return jsonify(items=[product_dict(r) for r in rows])
@app.get('/api/fashion/products')
def fashion_products():
 category=request.args.get('category','all'); q=request.args.get('q','').strip().lower(); c=db(); rows=c.execute('SELECT * FROM products ORDER BY id DESC').fetchall(); c.close(); items=[product_dict(r) for r in rows]
 if category and category!='all': items=[p for p in items if p.get('category')==category]
 if q: items=[p for p in items if q in p.get('name','').lower() or q in p.get('description','').lower()]
 return jsonify(items=items)
@app.get('/api/fashion/products/<int:pid>')
def fashion_product(pid):
 c=db(); r=c.execute('SELECT * FROM products WHERE id=?',(pid,)).fetchone(); c.close(); return (jsonify(product=product_dict(r)) if r else (jsonify(error='not_found'),404))
def _create_order():
 b=request.get_json(silent=True) or {}; name=str(b.get('customer_name','')).strip(); phone=str(b.get('phone','')).strip(); address=str(b.get('address','')).strip(); items=b.get('items',[]); total=float(b.get('total',0))
 if not name or not phone or not address or not isinstance(items,list) or not items:return jsonify(ok=False,error='missing_order_data'),400
 now=int(time.time()); c=db(); c.execute('INSERT INTO orders(customer_name,phone,address,items,total,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',(name,phone,address,json.dumps(items,ensure_ascii=False),'%.2f'%total,'Pending',now,now)); oid=c.lastrowid; c.commit(); c.close(); return jsonify(ok=True,order_id=oid)
@app.post('/api/orders')
def create_order(): return _create_order()
@app.post('/api/fashion/orders')
def fashion_order(): return _create_order()
def _stats():
 c=db(); out={'products':c.execute('SELECT COUNT(*) c FROM products').fetchone()['c'],'orders':c.execute('SELECT COUNT(*) c FROM orders').fetchone()['c'],'pending':c.execute("SELECT COUNT(*) c FROM orders WHERE status='Pending'").fetchone()['c'],'sales':float(c.execute("SELECT COALESCE(SUM(total),0) s FROM orders WHERE status!='Cancelled'").fetchone()['s'])}; c.close(); return out
@app.get('/api/admin/stats')
def stats():
 if not admin_ok(): return jsonify(error='unauthorized'),401
 return jsonify(**_stats())
@app.get('/api/fashion/admin/stats')
def fashion_stats():
 if not admin_ok(): return jsonify(error='unauthorized'),401
 return jsonify(**_stats())
def _admin_products():
 c=db(); rows=c.execute('SELECT * FROM products ORDER BY id DESC').fetchall(); c.close(); return [product_dict(r) for r in rows]
@app.get('/api/admin/products')
def admin_products():
 if not admin_ok(): return jsonify(error='unauthorized'),401
 return jsonify(items=_admin_products())
@app.get('/api/fashion/admin/products')
def fashion_admin_products():
 if not admin_ok(): return jsonify(error='unauthorized'),401
 return jsonify(items=_admin_products())
def _save_product(pid=None):
 if not admin_ok(): return jsonify(error='unauthorized'),401
 b=request.get_json(silent=True) or {}; name=str(b.get('name','')).strip(); now=int(time.time()); gallery=b.get('gallery',[])
 if not isinstance(gallery,list): gallery=[]
 gallery=[str(x).strip() for x in gallery if str(x).strip()][:6]; image=str(b.get('image') or b.get('image_url') or (gallery[0] if gallery else '')).strip()
 if image and image not in gallery: gallery.insert(0,image)
 if not name:return jsonify(error='name_required'),400
 vals=(name,str(b.get('category','')),float(b.get('price',0)),float(b.get('old_price',0) or 0),image,json.dumps(gallery,ensure_ascii=False),str(b.get('description','')),int(b.get('stock',0)),now)
 for attempt in range(5):
  c=None
  try:
   c=db()
   if pid is None:
    cur=c.execute('INSERT INTO products(name,category,price,old_price,image_url,gallery,description,stock,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)',vals+(now,)); pid=cur.lastrowid
   else:
    c.execute('UPDATE products SET name=?,category=?,price=?,old_price=?,image_url=?,gallery=?,description=?,stock=?,updated_at=? WHERE id=?',vals+(pid,))
   c.commit(); c.close(); return jsonify(ok=True,id=pid)
  except sqlite3.OperationalError as e:
   if c: c.rollback(); c.close()
   if 'locked' not in str(e).lower() or attempt==4: raise
   time.sleep(0.5*(attempt+1))
 return jsonify(error='database_locked'),503
@app.post('/api/admin/products')
def add_product(): return _save_product()
@app.post('/api/fashion/admin/products')
def fashion_add_product(): return _save_product()
@app.put('/api/admin/products/<int:pid>')
def edit_product(pid): return _save_product(pid)
@app.put('/api/fashion/admin/products/<int:pid>')
def fashion_edit_product(pid): return _save_product(pid)
def _delete_product(pid):
 if not admin_ok(): return jsonify(error='unauthorized'),401
 for attempt in range(5):
  c=None
  try:
   c=db(); c.execute('DELETE FROM products WHERE id=?',(pid,)); c.commit(); c.close(); return jsonify(ok=True)
  except sqlite3.OperationalError as e:
   if c: c.rollback(); c.close()
   if 'locked' not in str(e).lower() or attempt==4: raise
   time.sleep(0.5*(attempt+1))
 return jsonify(error='database_locked'),503
def _orders():
 c=db(); rows=c.execute('SELECT * FROM orders ORDER BY id DESC').fetchall(); c.close(); out=[]
 for r in rows:
  x=dict(r); x['items']=json.loads(x['items']); x['customer']=x['customer_name']; out.append(x)
 return out
@app.delete('/api/admin/products/<int:pid>')
def delete_product(pid): return _delete_product(pid)
@app.delete('/api/fashion/admin/products/<int:pid>')
def fashion_delete_product(pid): return _delete_product(pid)
@app.get('/api/admin/orders')
def admin_orders():
 if not admin_ok(): return jsonify(error='unauthorized'),401
 return jsonify(items=_orders())
@app.get('/api/fashion/admin/orders')
def fashion_admin_orders():
 if not admin_ok(): return jsonify(error='unauthorized'),401
 return jsonify(items=_orders())
def _update_order(oid):
 if not admin_ok(): return jsonify(error='unauthorized'),401
 status=str((request.get_json(silent=True) or {}).get('status','Pending')); allowed={'Pending','Confirmed','Processing','Shipped','Delivered','Cancelled'}
 if status not in allowed:return jsonify(error='invalid_status'),400
 for attempt in range(5):
  c=None
  try:
   c=db(); c.execute('UPDATE orders SET status=?,updated_at=? WHERE id=?',(status,int(time.time()),oid)); c.commit(); c.close(); return jsonify(ok=True)
  except sqlite3.OperationalError as e:
   if c: c.rollback(); c.close()
   if 'locked' not in str(e).lower() or attempt==4: raise
   time.sleep(0.5*(attempt+1))
 return jsonify(error='database_locked'),503
@app.put('/api/admin/orders/<int:oid>')
def update_order(oid): return _update_order(oid)
@app.put('/api/fashion/admin/orders/<int:oid>')
def fashion_update_order(oid): return _update_order(oid)
if __name__=='__main__': init_db(); app.run(host='0.0.0.0',port=PORT)