import os
from app import app, init_db, setup_webhook, PORT

if __name__ == '__main__':
    init_db()
    setup_webhook()
    app.run(host='0.0.0.0', port=PORT)
