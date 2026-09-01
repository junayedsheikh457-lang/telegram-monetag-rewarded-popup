import os, requests
from dotenv import load_dotenv
from flask import Flask, request

load_dotenv()
BOT_TOKEN=os.getenv('BOT_TOKEN','')
PORT=int(os.getenv('PORT','10000'))
RENDER_EXTERNAL_URL=os.getenv('RENDER_EXTERNAL_URL','').rstrip('/')
WEBHOOK_SECRET=os.getenv('WEBHOOK_SECRET','')
MINIAPP_URL=os.getenv('MINIAPP_URL') or RENDER_EXTERNAL_URL

app=Flask(__name__)

def telegram(method, payload):
    return requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/{method}', json=payload, timeout=20)

def send_start(chat_id):
    keyboard={'inline_keyboard':[[{'text':'🎁 অ্যাড দেখে রিওয়ার্ড নাও','web_app':{'url':MINIAPP_URL}}]]}
    telegram('sendMessage', {'chat_id':chat_id,'text':'স্বাগতম!\n\nনিচের বাটনে ক্লিক করে Mini App ওপেন করো এবং verified rewarded ad দেখে রিওয়ার্ড নাও।','reply_markup':keyboard})

@app.post('/telegram/webhook')
def webhook():
    if WEBHOOK_SECRET and request.headers.get('X-Telegram-Bot-Api-Secret-Token') != WEBHOOK_SECRET:
        return 'forbidden',403
    update=request.get_json(silent=True) or {}
    msg=update.get('message') or {}
    text=msg.get('text','')
    if text.startswith('/start'):
        send_start(msg.get('chat',{}).get('id'))
    return 'ok'

@app.get('/bot-health')
def bot_health(): return {'ok':True}

if __name__=='__main__':
    if not BOT_TOKEN:
        raise RuntimeError('BOT_TOKEN is required')
    if RENDER_EXTERNAL_URL:
        url=f'{RENDER_EXTERNAL_URL}/telegram/webhook'
        payload={'url':url}
        if WEBHOOK_SECRET: payload['secret_token']=WEBHOOK_SECRET
        r=telegram('setWebhook',payload)
        print('setWebhook:',r.text)
    app.run(host='0.0.0.0',port=PORT)
