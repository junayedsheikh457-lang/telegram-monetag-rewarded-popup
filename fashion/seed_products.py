import os, sqlite3, json, time

DB_PATH = os.getenv('DB_PATH', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data.db'))

# Starter catalog matching the luxury black/gold/pink reference. These are real DB products,
# so the Admin Panel can edit or delete them normally.
STARTER_PRODUCTS = [
    {
        'name': 'Embroidered A-Line Dress', 'category': '1 Piece', 'price': 2490, 'old_price': 3120,
        'image': 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=900&q=85',
        'description': 'Elegant embroidered A-line dress with a premium boutique finish.', 'stock': 10
    },
    {
        'name': 'Lace Detail Co-ord Set', 'category': '2 Piece', 'price': 2890, 'old_price': 3420,
        'image': 'https://images.unsplash.com/photo-1564257577054-3e0c7c8f3f1d?auto=format&fit=crop&w=900&q=85',
        'description': 'Chic lace-detail co-ord set designed for a refined modern look.', 'stock': 8
    },
    {
        'name': 'Printed Oversized Shirt', 'category': '1 Piece', 'price': 1790, 'old_price': 1990,
        'image': 'https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?auto=format&fit=crop&w=900&q=85',
        'description': 'Relaxed oversized printed shirt with an effortless premium style.', 'stock': 12
    },
    {
        'name': 'Floral Midi Dress', 'category': '1 Piece', 'price': 2690, 'old_price': 3590,
        'image': 'https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?auto=format&fit=crop&w=900&q=85',
        'description': 'Feminine floral midi dress for elegant everyday and occasion wear.', 'stock': 7
    }
]

def seed_products():
    c = sqlite3.connect(DB_PATH, timeout=60)
    c.execute('PRAGMA busy_timeout=60000')
    c.execute('PRAGMA journal_mode=WAL')
    count = c.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    if count == 0:
        now = int(time.time())
        for p in STARTER_PRODUCTS:
            c.execute('''INSERT INTO products
                (name,category,price,old_price,image_url,gallery,description,stock,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)''',
                (p['name'], p['category'], p['price'], p['old_price'], p['image'],
                 json.dumps([p['image']], ensure_ascii=False), p['description'], p['stock'], now, now))
        c.commit()
    c.close()

if __name__ == '__main__':
    seed_products()
