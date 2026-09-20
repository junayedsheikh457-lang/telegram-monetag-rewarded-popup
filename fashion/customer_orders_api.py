import json, time
from flask import jsonify, request
from app import app, DB_PATH
from fashion_backend import fdb

@app.after_request
def luxera_inject_orders_script(response):
    try:
        if request.path.rstrip('/') == '/fashion' and response.content_type.startswith('text/html'):
            body = response.get_data(as_text=True)
            tag = '<script src="/fashion/orders.js?v=2"></script>'
            if tag not in body:
                body = body.replace('</body>', tag + '</body>')
                response.set_data(body)
    except Exception:
        pass
    return response

def _public_order_dict(row):
    d = dict(row)
    try:
        d['items'] = json.loads(d.get('items') or '[]')
    except Exception:
        d['items'] = []
    d.pop('address', None)
    d.pop('phone', None)
    return d

@app.get('/api/fashion/my-orders')
def luxera_my_orders():
    phone = ''.join(ch for ch in str(request.args.get('phone', '')) if ch.isdigit() or ch == '+').strip()
    if len(phone) < 6:
        return jsonify(error='valid_phone_required'), 400
    c = fdb()
    rows = c.execute('SELECT * FROM orders WHERE phone=? ORDER BY id DESC LIMIT 100', (phone,)).fetchall()
    c.close()
    return jsonify(items=[_public_order_dict(r) for r in rows])

@app.post('/api/fashion/my-orders/cancel')
def luxera_cancel_my_order():
    b = request.get_json(silent=True) or {}
    phone = ''.join(ch for ch in str(b.get('phone', '')) if ch.isdigit() or ch == '+').strip()
    try:
        oid = int(b.get('order_id'))
    except Exception:
        return jsonify(error='valid_order_id_required'), 400
    if len(phone) < 6:
        return jsonify(error='valid_phone_required'), 400
    c = fdb()
    row = c.execute('SELECT * FROM orders WHERE id=? AND phone=?', (oid, phone)).fetchone()
    if not row:
        c.close()
        return jsonify(error='not_found'), 404
    if row['status'] not in ('Pending', 'Confirmed'):
        c.close()
        return jsonify(error='order_cannot_be_cancelled'), 409
    try:
        items = json.loads(row['items'] or '[]')
    except Exception:
        items = []
    now = int(time.time())
    for item in items:
        try:
            c.execute('UPDATE products SET stock=stock+?,updated_at=? WHERE id=?', (int(item.get('qty', 0)), now, int(item.get('id'))))
        except Exception:
            pass
    c.execute("UPDATE orders SET status='Cancelled',updated_at=? WHERE id=?", (now, oid))
    c.commit(); c.close()
    return jsonify(ok=True)
