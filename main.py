import random
import sqlite3
import datetime
import uuid
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, CommandHandler, InlineQueryHandler, ContextTypes

TOKEN = "توکن_خودت_اینجا"

conn = sqlite3.connect("axes.db", check_same_thread=False)
cursor = conn.cursor()

def get_title(size):
    if size < 30:
        return "🥚 جوجه تبر"
    elif size < 80:
        return "🪓 تبر باز"
    elif size < 100:
        return "🪓 تبرچی حرفه‌ای"
    else:
        return "👑 شاه تبر"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    now = datetime.date.today().isoformat()

    if chat.type == "private":
        await update.message.reply_text("این دستور فقط داخل گروه قابل استفاده است.")
        return

    cursor.execute("SELECT * FROM users WHERE user_id = ? AND group_id = ?", (user.id, chat.id))
    row = cursor.fetchone()

    if row:
        last_action = row[5]
        if last_action == now:
            await update.message.reply_text("🕒 امروز قبلاً تبرت رو امتحان کردی. فردا بیا!")
            return
        cursor.execute("UPDATE users SET axe_size = axe_size - 2 WHERE user_id = ? AND group_id = ?", (user.id, chat.id))
    else:
        cursor.execute("INSERT INTO users (user_id, group_id, username, first_name, last_action) VALUES (?, ?, ?, ?, ?)",
                       (user.id, chat.id, user.username or "?", user.first_name or "?", now))
        conn.commit()
        row = (user.id, chat.id, user.username, user.first_name, 0, now)

    growth = random.randint(-3, 10)
    new_size = max(0, row[4] + growth)

    cursor.execute("UPDATE users SET axe_size = ?, last_action = ? WHERE user_id = ? AND group_id = ?",
                   (new_size, now, user.id, chat.id))
    conn.commit()

    title = get_title(new_size)
    await update.message.reply_text(
        f"{user.first_name} امروز {growth} واحد به تبرش اضافه کرد!\n"
        f"🔢 تبر جدید: {new_size} واحد\n🏷️ لقب: {title}"
    )

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("این دستور فقط داخل گروه قابل استفاده است.")
        return

    cursor.execute("SELECT username, first_name, axe_size FROM users WHERE group_id = ? ORDER BY axe_size DESC LIMIT 10", (chat.id,))
    rows = cursor.fetchall()
    msg = "🏆 جدول تبرترین‌ها:\n\n"
    for i, row in enumerate(rows, 1):
        name = row[0] or row[1]
        msg += f"{i}. {name} - {row[2]} واحد\n"
    await update.message.reply_text(msg)

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = [
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="🪓 زدن تبر",
            input_message_content=InputTextMessageContent("/start"),
            description="ثبت امتیاز امروز",
        ),
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="📊 جدول رتبه",
            input_message_content=InputTextMessageContent("/top"),
            description="بررسی رتبه‌ها",
        ),
    ]
    await update.inline_query.answer(results, cache_time=1)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("top", top))
app.add_handler(InlineQueryHandler(inline_query))

print("ربات فعال شد")
await app.run_polling()
