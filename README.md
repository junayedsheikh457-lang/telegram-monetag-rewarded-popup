# Telegram Mini App + Monetag Rewarded Popup

এই প্রজেক্টে তুমি পাবে:
- Telegram Mini App (Rewarded Popup অ্যাডের জন্য)
- বেসিক Telegram Bot (Python)
- Monetag ইন্টিগ্রেশনের টেমপ্লেট

## Setup Steps

### 1. Monetag অ্যাকাউন্ট
1. https://monetag.com এ Publisher হিসেবে সাইন আপ করো
2. Telegram Mini App অ্যাড করো
3. **Rewarded Popup** zone তৈরি করো
4. যে SDK script পাবে সেটা কপি করো

### 2. Mini App হোস্ট করো
- `miniapp/` ফোল্ডারের কোড Vercel / Netlify / Railway-এ হোস্ট করো
- HTTPS লিংক লাগবে

### 3. Bot Setup
```bash
pip install -r requirements.txt
```

`.env` ফাইল তৈরি করো:
```
BOT_TOKEN=তোমার_বট_টোকেন
MINIAPP_URL=https://তোমার-miniapp-লিংক
```

তারপর রান করো:
```bash
python bot.py
```

### 4. Monetag Script বসাও
`miniapp/index.html` ফাইলে Monetag-এর script বসাবে (placeholder আছে)।

### গুরুত্বপূর্ণ
- `show_XXXXXX` জায়গায় Monetag যে function নাম দিয়েছে সেটা বসাবে
- `data-zone` এ তোমার zone ID বসাবে
- প্রোডাকশনে postback ব্যবহার করো (ফ্রড কমাতে)

## Structure
```
├── bot.py                 # Telegram Bot
├── requirements.txt
├── .env.example
├── miniapp/
│   ├── index.html         # Mini App frontend
│   └── style.css
└── README.md
```
