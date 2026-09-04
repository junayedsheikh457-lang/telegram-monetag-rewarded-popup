import os
from app import app, init_db, PORT
from fashion.seed_products import seed_products
from fashion.gallery_seed import seed_galleries

if __name__ == '__main__':
    init_db()
    seed_products()
    seed_galleries()
    app.run(host='0.0.0.0', port=PORT)
