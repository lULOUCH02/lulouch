import yfinance as yf
import pandas as pd
import ta
import requests
import feedparser
from urllib.parse import urlparse
from datetime import datetime, timedelta
import pytz
from dateutil import parser

# 🕒 الإعداد الزمني
local_tz = pytz.timezone("Asia/Riyadh")
now = datetime.now(local_tz)
start_time = local_tz.localize(datetime(now.year, now.month, now.day, 0, 0))
end_time = now

# 🎯 تحليل المشاعر بالكلمات المفتاحية (خفيف)
positive_keywords = ["bullish", "buy", "positive", "surge", "rally", "increase", "pump"]
negative_keywords = ["bearish", "sell", "negative", "drop", "crash", "decrease", "dump"]

def classify_sentiment(text):
    text_lower = text.lower()
    if any(word in text_lower for word in positive_keywords):
        return "إيجابي"
    elif any(word in text_lower for word in negative_keywords):
        return "سلبي"
    else:
        return "محايد"

def is_bitcoin_related(title, summary, link=""):
    text = (title + " " + summary).lower()
    parsed_url = urlparse(link)
    path_text = parsed_url.path.lower()
    keywords = ["bitcoin", "btc"]
    return any(keyword in (text + " " + path_text) for keyword in keywords)

# 📰 مصادر الأخبار
rss_feeds = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://cryptoslate.com/feed/",
    "https://news.bitcoin.com/feed/",
    "https://decrypt.co/feed",
    "https://u.today/rss",
    "https://bitcoinmagazine.com/.rss/full/",
    "https://www.newsbtc.com/feed/",
    "https://www.investing.com/rss/news_285.rss",
    "https://www.fxstreet.com/rss/cryptocurrencies",
    "https://ambcrypto.com/feed/",
    "https://cryptobriefing.com/feed/",
    "https://www.cryptopolitan.com/feed/",
    "https://coinjournal.net/feed/",
    "https://www.ccn.com/crypto/feed/",
    "https://www.blockonomi.com/feed/",
    "https://www.livebitcoinnews.com/feed/",
    "https://cryptonews.com/news/feed/",
]

positive_news, negative_news = 0, 0
for url in rss_feeds:
    feed = feedparser.parse(url)
    for entry in feed.entries:
        published_str = getattr(entry, 'published', None)
        if not published_str:
            continue
        published = parser.parse(published_str).astimezone(local_tz)
        if not (start_time <= published <= end_time):
            continue
        title = getattr(entry, 'title', '')
        link = getattr(entry, 'link', '')
        summary = getattr(entry, 'summary', title)
        if not is_bitcoin_related(title, summary, link):
            continue
        sentiment = classify_sentiment(summary)
        if sentiment == "إيجابي":
            positive_news += 1
        elif sentiment == "سلبي":
            negative_news += 1

# 💰 تحليل السوق اللحظي
btc = yf.download("BTC-USD", period="2d", interval="1h")
close = btc["Close"].squeeze()
price_now = close.iloc[-1]
price_prev = close.iloc[-2]
price_change_pct = ((price_now - price_prev) / price_prev) * 100

rsi = ta.momentum.RSIIndicator(close=close).rsi().iloc[-1]
macd = ta.trend.MACD(close=close)
macd_line = macd.macd().iloc[-1]
macd_signal = macd.macd_signal().iloc[-1]

# 🧠 مؤشر المزاج اللحظي
score = 50
if price_change_pct > 2:
    score += 10
elif price_change_pct < -2:
    score -= 10

if rsi > 70:
    score -= 10
elif rsi < 30:
    score += 10

if macd_line > macd_signal:
    score += 5
else:
    score -= 5

score += (positive_news - negative_news) * 3
score = max(0, min(score, 100))

if score > 70:
    recommendation = "🚀 السوق متفائل جدًا (فكر بالبيع)"
elif score < 30:
    recommendation = "🧊 السوق خائف (فرصة شراء)"
else:
    recommendation = "⏳ السوق متوازن أو غير واضح"

print("\n📅 التوقيت:", now.strftime("%Y-%m-%d %H:%M"))
print(f"💰 السعر الحالي: ${price_now:,.2f} ({price_change_pct:+.2f}%)")
print(f"📰 الأخبار: إيجابية: {positive_news}, سلبية: {negative_news}")
print(f"📊 RSI: {rsi:.2f} | MACD: {macd_line:.2f} / {macd_signal:.2f}")
print(f"\n🧠 مؤشر المزاج اللحظي: {score}/100")
print(f"📍 التوصية: {recommendation}")
