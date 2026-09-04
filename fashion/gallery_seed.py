import sqlite3, json, os, time

DB_PATH=os.getenv('DB_PATH',os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'data.db'))
POOL=[
'https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1564257577054-3e0c7c8f3f1d?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1566174053879-31528523f8ae?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1591369822096-ffd140ec948f?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1485968579580-b6d095142e6e?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1525507119028-ed4c629a60a3?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1485230895905-ec40ba36b9bc?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1496217590455-aa63a8350eea?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?auto=format&fit=crop&w=900&q=85',
'https://images.unsplash.com/photo-1523381210434-271e8be1f52b?auto=format&fit=crop&w=900&q=85'
]

def seed_galleries():
    c=sqlite3.connect(DB_PATH,timeout=60)
    c.execute('PRAGMA busy_timeout=60000')
    rows=c.execute('SELECT id,image_url FROM products ORDER BY id').fetchall()
    now=int(time.time())
    for idx,(pid,main) in enumerate(rows):
        imgs=[main] if main else []
        for step in range(1,8):
            u=POOL[(idx+step)%len(POOL)]
            if u not in imgs: imgs.append(u)
            if len(imgs)>=5: break
        c.execute('UPDATE products SET gallery=?,updated_at=? WHERE id=?',(json.dumps(imgs,ensure_ascii=False),now,pid))
    c.commit(); c.close()
