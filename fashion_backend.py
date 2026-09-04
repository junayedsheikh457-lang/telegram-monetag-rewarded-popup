import os, sqlite3, time, json, hmac
from flask import jsonify, request, send_from_directory
from app import app, DB_PATH, ADMIN_PASSWORD

FASHION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fashion')
STATUSES = ('Pending', 'Confirmed', 'Processing', 'Shipped', 'Delivered', 'Cancelled')

def fdb():
    c = sqlite3.connect(DB_PATH, timeout=20)
    c.row_factory = sqlite3.Row
    return c

def init_fashion_db():
    c = fdb()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS products(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      category TEXT NOT NULL,
      price REAL NOT NULL,
      old_price REAL NOT NULL DEFAULT 0,
      image TEXT NOT NULL DEFAULT '',
      stock INTEGER NOT NULL DEFAULT 0,
      description TEXT NOT NULL DEFAULT '',
      active INTEGER NOT NULL DEFAULT 1,
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS orders(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      customer TEXT NOT NULL,
      phone TEXT NOT NULL,
      address TEXT NOT NULL,
      items TEXT NOT NULL,
      total REAL NOT NULL,
      status TEXT NOT NULL DEFAULT 'Pending',
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_products_active ON products(active, category);
    CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status, created_at);
    ''')
    # The main app's fashion admin routes use image_url + gallery. Older fashion
    # databases were created with only image, so migrate them before requests.
    columns = {row['name'] for row in c.execute('PRAGMA table_info(products)').fetchall()}
    if 'image_url' not in columns:
        c.execute("ALTER TABLE products ADD COLUMN image_url TEXT DEFAULT ''")
    if 'gallery' not in columns:
        c.execute("ALTER TABLE products ADD COLUMN gallery TEXT DEFAULT '[]'")
    if 'image' in columns:
        c.execute("UPDATE products SET image_url=COALESCE(NULLIF(image_url,''), image) WHERE image_url IS NULL OR image_url='' OR image_url=''")
    c.execute("UPDATE products SET gallery=json_array(image_url) WHERE (gallery IS NULL OR gallery='' OR gallery='[]') AND image_url IS NOT NULL AND image_url!=''")
    if c.execute('SELECT COUNT(*) AS n FROM products').fetchone()['n'] == 0:
        now = int(time.time())
        seed = [
          ('Elegant Three Piece','3 Piece',899,1199,'',12,'Premium three piece dress',1),
          ('Premium Two Piece','2 Piece',749,999,'',15,'Comfortable two piece set',1),
          ('Stylish One Piece','1 Piece',699,899,'',10,'Modern everyday one piece',1),
          ('Floral Three Piece','3 Piece',999,1399,'',8,'Floral print three piece',1),
          ('Classic Abaya','Abaya',1099,1499,'',9,'Elegant modest abaya',1),
          ('Modern One Piece','1 Piece',799,999,'',14,'Smart casual one piece',1),
          ('Premium Two Piece','2 Piece',849,1099,'',11,'Premium fabric two piece',1),
          ('Party Wear Three Piece','3 Piece',1299,1699,'',6,'Party wear collection',1),
          ('Daily Wear One Piece','1 Piece',649,849,'',20,'Daily comfort collection',1),
          ('Elegant Abaya','Abaya',1199,1599,'',7,'Premium elegant abaya',1),
          ('Special Offer Dress','Offer',599,899,'',18,'Limited time offer',1),
          ('Luxury Three Piece','3 Piece',1499,1999,'',5,'Luxury festive collection',1)
        ]
        c.executemany('INSERT INTO products(name,category,price,old_price,image,stock,description,active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)', [x+(now,now) for x in seed])
    c.commit(); c.close()

def admin_ok():
    supplied = request.headers.get('X-Admin-Password','')
    return bool(ADMIN_PASSWORD) and hmac.compare_digest(supplied, ADMIN_PASSWORD)

def require_admin():
    if not admin_ok():
        return jsonify(error='unauthorized'), 401
    return None

def product_dict(r):
    d = dict(r)
    d['active'] = bool(d['active'])
    return d

@app.get('/fashion')
@app.get('/fashion/')
def fashion_home():
    return send_from_directory(FASHION_DIR, 'index.html')

@app.get('/fashion/admin')
@app.get('/fashion/admin/')
def fashion_admin():
    return send_from_directory(FASHION_DIR, 'admin.html')

@app.get('/api/fashion/products')
def fashion_products():
    category = request.args.get('category','all')
    q = request.args.get('q','').strip().lower()
    c = fdb()
    rows = c.execute('SELECT * FROM products WHERE active=1 ORDER BY id DESC').fetchall()
    c.close()
    out=[]
    for r in rows:
        d=product_dict(r)
        if category != 'all' and d['category'] != category: continue
        if q and q not in d['name'].lower() and q not in d['description'].lower(): continue
        out.append(d)
    return jsonify(items=out)

@app.get('/api/fashion/admin/stats')
def fashion_stats():
    err=require_admin()
    if err:return err
    c=fdb()
    products=c.execute('SELECT COUNT(*) n FROM products').fetchone()['n']
    orders=c.execute('SELECT COUNT(*) n FROM orders').fetchone()['n']
    pending=c.execute("SELECT COUNT(*) n FROM orders WHERE status='Pending'").fetchone()['n']
    sales=c.execute("SELECT COALESCE(SUM(total),0) n FROM orders WHERE status!='Cancelled'").fetchone()['n']
    c.close()
    return jsonify(products=products,orders=orders,pending=pending,sales=float(sales))

@app.get('/api/fashion/admin/products')
def fashion_admin_products():
    err=require_admin()
    if err:return err
    c=fdb(); rows=c.execute('SELECT * FROM products ORDER BY id DESC').fetchall(); c.close()
    return jsonify(items=[product_dict(r) for r in rows])

@app.post('/api/fashion/admin/products')
def fashion_admin_product_create():
    err=require_admin()
    if err:return err
    b=request.get_json(silent=True) or {}
    name=str(b.get('name','')).strip(); category=str(b.get('category','1 Piece')).strip()
    try: price=float(b.get('price',0)); old=float(b.get('old_price',0) or 0); stock=int(b.get('stock',0) or 0)
    except (TypeError,ValueError): return jsonify(error='invalid_number'),400
    if not name or price <= 0 or stock < 0:return jsonify(error='invalid_product'),400
    now=int(time.time()); c=fdb(); cur=c.execute('INSERT INTO products(name,category,price,old_price,image,stock,description,active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(name,category,price,old,str(b.get('image','')).strip(),stock,str(b.get('description','')).strip(),1,now,now)); c.commit(); pid=cur.lastrowid; c.close()
    return jsonify(ok=True,id=pid),201

@app.put('/api/fashion/admin/products/<int:pid>')
def fashion_admin_product_update(pid):
    err=require_admin()
    if err:return err
    b=request.get_json(silent=True) or {}
    name=str(b.get('name','')).strip(); category=str(b.get('category','1 Piece')).strip()
    try: price=float(b.get('price',0)); old=float(b.get('old_price',0) or 0); stock=int(b.get('stock',0) or 0)
    except (TypeError,ValueError): return jsonify(error='invalid_number'),400
    if not name or price <= 0 or stock < 0:return jsonify(error='invalid_product'),400
    now=int(time.time()); c=fdb(); cur=c.execute('UPDATE products SET name=?,category=?,price=?,old_price=?,image=?,stock=?,description=?,updated_at=? WHERE id=?',(name,category,price,old,str(b.get('image','')).strip(),stock,str(b.get('description','')).strip(),now,pid)); c.commit(); c.close()
    if cur.rowcount != 1:return jsonify(error='not_found'),404
    return jsonify(ok=True)

@app.delete('/api/fashion/admin/products/<int:pid>')
def fashion_admin_product_delete(pid):
    err=require_admin()
    if err:return err
    c=fdb(); cur=c.execute('DELETE FROM products WHERE id=?',(pid,)); c.commit(); c.close()
    if cur.rowcount != 1:return jsonify(error='not_found'),404
    return jsonify(ok=True)

@app.post('/api/fashion/orders')
def fashion_create_order():
    b=request.get_json(silent=True) or {}
    customer=str(b.get('customer','')).strip(); phone=str(b.get('phone','')).strip(); address=str(b.get('address','')).strip(); raw=b.get('items') or []
    if not customer or not phone or not address or not isinstance(raw,list) or not raw:return jsonify(error='customer_phone_address_items_required'),400
    c=fdb()
    try:
        clean=[]; total=0.0
        for item in raw:
            pid=int(item.get('id')); qty=int(item.get('qty',1))
            if qty < 1 or qty > 50: raise ValueError('invalid_qty')
            p=c.execute('SELECT id,name,price,stock,active FROM products WHERE id=?',(pid,)).fetchone()
            if not p or not p['active'] or p['stock'] < qty: raise ValueError('stock_unavailable')
            line=round(float(p['price'])*qty,2); total += line
            clean.append({'id':p['id'],'name':p['name'],'price':float(p['price']),'qty':qty,'line_total':line})
        now=int(time.time())
        for item in clean:
            cur=c.execute('UPDATE products SET stock=stock-?,updated_at=? WHERE id=? AND stock>=?',(item['qty'],now,item['id'],item['qty']))
            if cur.rowcount != 1: raise ValueError('stock_changed')
        cur=c.execute('INSERT INTO orders(customer,phone,address,items,total,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',(customer,phone,address,json.dumps(clean,ensure_ascii=False),round(total,2),'Pending',now,now))
        c.commit(); oid=cur.lastrowid
    except ValueError as e:
        c.rollback(); c.close(); return jsonify(error=str(e)),409
    except Exception:
        c.rollback(); c.close(); return jsonify(error='order_failed'),500
    c.close(); return jsonify(ok=True,order_id=oid,total=round(total,2)),201

@app.get('/api/fashion/admin/orders')
def fashion_admin_orders():
    err=require_admin()
    if err:return err
    c=fdb(); rows=c.execute('SELECT * FROM orders ORDER BY id DESC LIMIT 500').fetchall(); c.close()
    out=[]
    for r in rows:
        d=dict(r)
        try:d['items']=json.loads(d['items'])
        except Exception:d['items']=[]
        out.append(d)
    return jsonify(items=out)

@app.put('/api/fashion/admin/orders/<int:oid>')
def fashion_admin_order_update(oid):
    err=require_admin()
    if err:return err
    b=request.get_json(silent=True) or {}; status=str(b.get('status','')).strip()
    if status not in STATUSES:return jsonify(error='invalid_status'),400
    c=fdb(); cur=c.execute('UPDATE orders SET status=?,updated_at=? WHERE id=?',(status,int(time.time()),oid)); c.commit(); c.close()
    if cur.rowcount != 1:return jsonify(error='not_found'),404
    return jsonify(ok=True)

if __name__ == '__main__':
    from app import init_db, setup_webhook, PORT
    init_db(); init_fashion_db(); setup_webhook(); app.run(host='0.0.0.0',port=PORT)
