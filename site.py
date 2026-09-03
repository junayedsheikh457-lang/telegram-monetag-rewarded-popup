from app import app, init_db, setup_webhook, PORT
from fashion_backend import init_fashion_db

if __name__ == '__main__':
    init_db()
    init_fashion_db()
    setup_webhook()
    app.run(host='0.0.0.0', port=PORT)
