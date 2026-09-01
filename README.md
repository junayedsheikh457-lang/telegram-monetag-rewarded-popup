# Telegram Mini App + Monetag Rewarded Popup

Render Free-তে চালানোর জন্য Telegram Mini App + Monetag Rewarded Popup backend।

### Features
- Telegram Mini App UI
- Monetag zone `11677828`
- Telegram `initData` server-side validation
- Server-side balance
- Reward history
- One-time pending ad session
- Postback-based reward credit
- Duplicate/cooldown protection
- Simple admin dashboard
- Telegram webhook

### Render deployment
1. GitHub repo থেকে Render-এ **Web Service** তৈরি করো।
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `python app.py`
4. Environment variables যোগ করো:
   - `BOT_TOKEN` = BotFather token
   - `ADMIN_PASSWORD` = নিজের admin password
   - `POSTBACK_SECRET` = নিজের random secret
   - `WEBHOOK_SECRET` = নিজের random secret
   - `REWARD_PER_AD` = `0.05`
   - `AD_COOLDOWN_SECONDS` = `30`
5. Deploy হওয়ার পরে Render URL-টাই `MINIAPP_URL` হিসেবে দিতে পারো। `RENDER_EXTERNAL_URL` থাকলে webhook নিজে সেট হবে।

### Monetag postback
Mini App ad চালুর সময় Telegram user ID `ymid` হিসেবে পাঠানো হচ্ছে। Monetag dashboard-এ postback URL configure করতে হবে এবং তোমার Monetag-এর actual postback parameter names অনুযায়ী `user_id`/`ymid` mapping করতে হবে। এই server endpoint হলো:

`https://YOUR-SERVICE.onrender.com/monetag/postback?secret=YOUR_POSTBACK_SECRET&user_id={ymid}&event_id={event_id}`

**নোট:** Monetag-এর dashboard যে exact postback macro/parameter দেয় সেটাই ব্যবহার করবে; কোনো macro অনুমান করে বসাবে না।

### Admin
`https://YOUR-SERVICE.onrender.com/admin` খুলে password দিয়ে dashboard ব্যবহার করো।

### Important
Render-এর free filesystem persistent database হিসেবে ধরা উচিত নয়। Testing-এর জন্য SQLite ঠিক আছে; production-এ balance/withdrawal data স্থায়ী রাখতে external PostgreSQL (যেমন Neon) connect করা উচিত।
