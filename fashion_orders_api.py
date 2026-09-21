import json, time, secrets, sqlite3
from flask import request, jsonify
from app import app, DB_PATH


def _db():
    c = sqlite3.connect(DB_PATH, timeout=20)
    c.row_factory = sqlite3.Row
    return c


def init_order_history_db():
    c = _db()
    cols = {r['name'] for r in c.execute('PRAGMA table_info(orders)').fetchall()}
    if 'public_token' not in cols:
        c.execute('ALTER TABLE orders ADD COLUMN public_token TEXT')
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_public_token ON orders(public_token)")
    c.commit()
    c.close()


def _items(row):
    try:
        return json.loads(row['items'] or '[]')
    except Exception:
        return []


@app.get('/api/fashion/my-orders')
def fashion_my_orders():
    phone = (request.args.get('phone') or '').strip()
    if not phone:
        return jsonify(error='phone_required'), 400
    c = _db()
    rows = c.execute('SELECT * FROM orders WHERE phone=? ORDER BY id DESC LIMIT 100', (phone,)).fetchall()
    c.close()
    out = []
    for row in rows:
        d = dict(row)
        d['items'] = _items(row)
        out.append(d)
    return jsonify(items=out)


@app.post('/api/fashion/my-orders/cancel')
def fashion_cancel_my_order():
    body = request.get_json(silent=True) or {}
    phone = str(body.get('phone') or '').strip()
    try:
        order_id = int(body.get('order_id'))
    except (TypeError, ValueError):
        return jsonify(error='invalid_order_id'), 400
    if not phone:
        return jsonify(error='phone_required'), 400
    c = _db()
    row = c.execute('SELECT * FROM orders WHERE id=? AND phone=?', (order_id, phone)).fetchone()
    if not row:
        c.close()
        return jsonify(error='not_found'), 404
    if row['status'] not in ('Pending', 'Confirmed'):
        c.close()
        return jsonify(error='order_cannot_be_cancelled'), 409
    items = _items(row)
    now = int(time.time())
    for item in items:
        try:
            qty = int(item.get('qty', 0)); pid = int(item.get('id'))
        except (TypeError, ValueError):
            continue
        if qty > 0:
            c.execute('UPDATE products SET stock=stock+?, updated_at=? WHERE id=?', (qty, now, pid))
    c.execute("UPDATE orders SET status='Cancelled', updated_at=? WHERE id=?", (now, order_id))
    c.commit(); c.close()
    return jsonify(ok=True, order_id=order_id, status='Cancelled')


@app.after_request
def inject_order_history_script(response):
    if request.path in ('/fashion', '/fashion/') and response.status_code == 200:
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            body = response.get_data(as_text=True)
            tag = '<script src="/fashion/orders.js?v=3"></script>'
            if tag not in body:
                body = body.replace('</body>', tag + '</body>')
                response.set_data(body)
    return response


@app.get('/fashion/orders.js')
def fashion_orders_script():
    from flask import send_from_directory
    import os
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fashion')
    return send_from_directory(folder, 'orders.js')
