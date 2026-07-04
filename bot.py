import os
import re
import logging
from collections import Counter
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def analyze_text(text: str) -> dict:
    words = re.findall(r"\b\w+\b", text.lower())
    sentences = re.split(r"[.!?]+", text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    characters_no_spaces = len(text.replace(" ", "").replace("\n", ""))
    word_freq = Counter(words)
    top_words = word_freq.most_common(5)

    return {
        "word_count": len(words),
        "unique_words": len(set(words)),
        "char_count": len(text),
        "char_no_spaces": characters_no_spaces,
        "sentence_count": len(sentences),
        "paragraph_count": len([p for p in text.split("\n\n") if p.strip()]),
        "avg_word_length": round(sum(len(w) for w in words) / len(words), 2) if words else 0,
        "top_words": top_words,
    }


def format_response(stats: dict) -> str:
    top = "\n".join(
        f"  {i+1}. *{word}* — {count}x"
        for i, (word, count) in enumerate(stats["top_words"])
    )

    return (
        f"📊 *Word Count Analysis*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 *Words:* {stats['word_count']}\n"
        f"🔤 *Unique words:* {stats['unique_words']}\n"
        f"💬 *Sentences:* {stats['sentence_count']}\n"
        f"📄 *Paragraphs:* {stats['paragraph_count']}\n"
        f"🔢 *Characters (with spaces):* {stats['char_count']}\n"
        f"🔡 *Characters (no spaces):* {stats['char_no_spaces']}\n"
        f"📏 *Avg word length:* {stats['avg_word_length']} letters\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 *Top {len(stats['top_words'])} words:*\n{top}"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Hello! I'm your *Word Counter Bot*.\n\n"
        "Just send me any text and I'll instantly count:\n"
        "• Total words & unique words\n"
        "• Sentences & paragraphs\n"
        "• Characters (with/without spaces)\n"
        "• Average word length\n"
        "• Top 5 most used words\n\n"
        "📎 You can also send me a *text file* (.txt) and I'll analyze it!\n\n"
        "Commands:\n"
        "/start — Show this message\n"
        "/help — How to use the bot\n"
        "/about — About this bot",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🆘 *How to use Word Counter Bot*\n\n"
        "1️⃣ *Analyze text* — Just type or paste any text and send it.\n\n"
        "2️⃣ *Analyze a file* — Send a `.txt` file and the bot will read and analyze it.\n\n"
        "3️ *Quick count* — Use `/count your text here` for a quick word count.\n\n"
        "That's it! No setup needed. 🚀",
        parse_mode="Markdown",
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "ℹ️ *About Word Counter Bot*\n\n"
        "A simple, fast Telegram bot that analyzes text and gives you detailed word count statistics.\n\n"
        "Built with Python & python-telegram-bot.\n"
        "Hosted on Railway. 🚂",
        parse_mode="Markdown",
    )


async def count_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text(
            "⚠️ Please provide text after the command.\nExample: `/count Hello world`",
            parse_mode="Markdown",
        )
        return
    stats = analyze_text(text)
    await update.message.reply_text(format_response(stats), parse_mode="Markdown")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if len(text.strip()) == 0:
        await update.message.reply_text("⚠️ Please send some text to analyze.")
        return
    stats = analyze_text(text)
    await update.message.reply_text(format_response(stats), parse_mode="Markdown")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    doc = update.message.document
    if not doc.file_name.endswith(".txt"):
        await update.message.reply_text(
            "⚠️ I can only analyze `.txt` files. Please send a plain text file.",
            parse_mode="Markdown",
        )
        return

    if doc.file_size > 1_000_000:
        await update.message.reply_text("⚠️ File is too large. Please keep it under 1 MB.")
        return

    await update.message.reply_text("⏳ Reading your file...")
    file = await doc.get_file()
    content = await file.download_as_bytearray()

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    if not text.strip():
        await update.message.reply_text("⚠️ The file appears to be empty.")
        return

    stats = analyze_text(text)
    await update.message.reply_text(
        f"📂 *File:* `{doc.file_name}`\n\n" + format_response(stats),
        parse_mode="Markdown",
    )


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("count", count_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
