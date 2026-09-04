import os, sqlite3, json, time

DB_PATH = os.getenv('DB_PATH', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data.db'))

STARTER_PRODUCTS = [
{'name':'Embroidered A-Line Dress','category':'Dresses','price':2490,'old_price':3120,'image':'https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=900&q=85','description':'Elegant embroidered A-line dress with a premium boutique finish.','stock':10},
{'name':'Lace Detail Co-ord Set','category':'Co-ords','price':2890,'old_price':3420,'image':'https://images.unsplash.com/photo-1564257577054-3e0c7c8f3f1d?auto=format&fit=crop&w=900&q=85','description':'Chic lace-detail co-ord set designed for a refined modern look.','stock':8},
{'name':'Printed Oversized Shirt','category':'Tops','price':1790,'old_price':1990,'image':'https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?auto=format&fit=crop&w=900&q=85','description':'Relaxed oversized printed shirt with an effortless premium style.','stock':12},
{'name':'Floral Midi Dress','category':'Dresses','price':2690,'old_price':3590,'image':'https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?auto=format&fit=crop&w=900&q=85','description':'Feminine floral midi dress for elegant everyday and occasion wear.','stock':7},
{'name':'Cotton Kurti Set','category':'Tops','price':1990,'old_price':2420,'image':'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?auto=format&fit=crop&w=900&q=85','description':'Soft cotton kurti set for everyday wear.','stock':22},
{'name':'Embroidered Long Kurta','category':'Tops','price':2190,'old_price':2790,'image':'https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=900&q=85','description':'Embroidered long kurta with a polished boutique finish.','stock':14},
{'name':'Satin Evening Dress','category':'Dresses','price':3290,'old_price':3990,'image':'https://images.unsplash.com/photo-1566174053879-31528523f8ae?auto=format&fit=crop&w=900&q=85','description':'Elegant satin evening dress for special occasions.','stock':10},
{'name':'Classic Wide Leg Pants','category':'Bottoms','price':1690,'old_price':1990,'image':'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=900&q=85','description':'Comfortable classic wide-leg pants.','stock':19},
{'name':'Luxury Black Abaya','category':'Dresses','price':2790,'old_price':3290,'image':'https://images.unsplash.com/photo-1591369822096-ffd140ec948f?auto=format&fit=crop&w=900&q=85','description':'Luxury modest black abaya with an elegant silhouette.','stock':9},
{'name':'Rose Pink Co-ord','category':'Co-ords','price':2590,'old_price':3090,'image':'https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=900&q=85','description':'Soft rose pink coordinated set for a modern feminine look.','stock':13},
{'name':'Pleated Maxi Dress','category':'Dresses','price':2390,'old_price':2990,'image':'https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=900&q=85','description':'Flowy pleated maxi dress with a timeless silhouette.','stock':16},
{'name':'Premium Casual Top','category':'Tops','price':1290,'old_price':1590,'image':'https://images.unsplash.com/photo-1485968579580-b6d095142e6e?auto=format&fit=crop&w=900&q=85','description':'Premium casual top for everyday styling.','stock':30},
{'name':'Elegant Party Gown','category':'Dresses','price':3890,'old_price':4590,'image':'https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?auto=format&fit=crop&w=900&q=85','description':'Statement party gown for elegant occasions.','stock':7},
{'name':'Denim Straight Jeans','category':'Bottoms','price':1890,'old_price':2290,'image':'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=900&q=85','description':'Classic straight-fit denim jeans.','stock':17},
{'name':'Modest Printed Abaya','category':'Dresses','price':2390,'old_price':2890,'image':'https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?auto=format&fit=crop&w=900&q=85','description':'Printed modest abaya with a graceful premium look.','stock':11},
{'name':'New Season Shirt Set','category':'Co-ords','price':2290,'old_price':2690,'image':'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=900&q=85','description':'Fresh new-season shirt set.','stock':12},
{'name':'Velvet Party Dress','category':'Dresses','price':3490,'old_price':4290,'image':'https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=900&q=85','description':'Rich velvet party dress with a premium finish.','stock':9},
{'name':'Silk Blouse','category':'Tops','price':1890,'old_price':2290,'image':'https://images.unsplash.com/photo-1485968579580-b6d095142e6e?auto=format&fit=crop&w=900&q=85','description':'Elegant silk-look blouse for polished styling.','stock':15},
{'name':'High Rise Trousers','category':'Bottoms','price':1990,'old_price':2390,'image':'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?auto=format&fit=crop&w=900&q=85','description':'Tailored high-rise trousers with a clean silhouette.','stock':18},
{'name':'Chic Summer Co-ord','category':'Co-ords','price':2190,'old_price':2590,'image':'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=900&q=85','description':'Lightweight summer co-ord set.','stock':20}
]

def seed_products():
    c = sqlite3.connect(DB_PATH, timeout=60)
    c.execute('PRAGMA busy_timeout=60000')
    try: c.execute('PRAGMA journal_mode=WAL')
    except sqlite3.OperationalError: pass
    now = int(time.time())
    existing = {r[0] for r in c.execute('SELECT name FROM products').fetchall()}
    for p in STARTER_PRODUCTS:
        if p['name'] in existing: continue
        c.execute('''INSERT INTO products
            (name,category,price,old_price,image_url,gallery,description,stock,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (p['name'],p['category'],p['price'],p['old_price'],p['image'],json.dumps([p['image']],ensure_ascii=False),p['description'],p['stock'],now,now))
    c.commit(); c.close()

if __name__ == '__main__': seed_products()
