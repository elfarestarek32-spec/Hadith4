#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sown Bot – Telegram Video/Story Downloader
Developer: Tariq | WhatsApp: +201019667530
"""

import os
import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from downloader import process_telegram_link  # ملف مساعد سيتم إرساله لاحقاً

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 ميجا (حد تيليجرام للبوتات)

# إعداد السجلات
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# رسالة البداية الإبداعية
START_TEXT = (
    "✨ <b>مرحباً بك في بوت Sown الأسطوري!</b> ✨\n\n"
    "🎥 <b>أنا هنا لأحمّل لك أي فيديو أو ستوري من تيليجرام بكل سهولة.</b>\n\n"
    "🔹 <b>كيف تستخدمني؟</b>\n"
    "▫️ أرسل رابط منشور فيديو من قناة عامة أو رابط الحساب (للستوريز إذا كان عاماً).\n"
    "▫️ سأقوم بجلب الملف لك فوراً بأعلى جودة.\n\n"
    "⚠️ <b>تنبيه هام:</b> <i>يمنع استخدام هذا البوت في أي محتوى يغضب الله تعالى، ولن يتسامح المطور مع أي استخدام غير أخلاقي أو غير قانوني.</i>\n\n"
    "👨‍💻 <b>المطور:</b> <code>Tariq</code>\n"
    "📞 <b>للتواصل واتساب:</b> <code>+201019667530</code>"
)

HELP_TEXT = (
    "🆘 <b>مساعدة Sown:</b>\n\n"
    "• أرسل رابط منشور (t.me/xxxx/123) لتحميل الفيديو.\n"
    "• أرسل رابط حساب عام (t.me/username) لتحميل الستوري إن كان متاحاً.\n"
    "• البوت يدعم الروابط العامة فقط حالياً.\n\n"
    "⚡ <b>أزرار سريعة:</b>"
)

# لوحة أزرار أنيقة بألوان تيليجرام الجديدة (محاكاة باستخدام إيموجي)
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌟 تحميل فيديو", callback_data="help_video")],
        [InlineKeyboardButton("📸 تحميل ستوري", callback_data="help_story")],
        [InlineKeyboardButton("📞 تواصل واتساب", url="https://wa.me/201019667530")],
        [InlineKeyboardButton("👨‍💻 المطور Tariq", url="https://t.me/Tariq_official")]  # يمكن تعديله
    ])

# أوامر البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        START_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard()
    )

# معالجة استفسارات الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "help_video":
        await query.edit_message_text(
            "📥 <b>تحميل فيديو:</b>\n\n"
            "أرسل رابط المنشور مباشرة.\n"
            "مثال: <code>https://t.me/channelname/123</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
            ])
        )
    elif query.data == "help_story":
        await query.edit_message_text(
            "📸 <b>تحميل ستوري:</b>\n\n"
            "أرسل رابط الحساب العام (إذا كان يسمح بمشاهدة الستوري للعامة).\n"
            "مثال: <code>https://t.me/username</code>\n"
            "سيقوم البوت بمحاولة جلب الستوري الحالي.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
            ])
        )
    elif query.data == "back_main":
        await query.edit_message_text(
            START_TEXT,
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_keyboard()
        )

# استقبال الروابط ومعالجتها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.startswith("http://") or text.startswith("https://"):
        # التحقق إذا كان رابط تيليجرام
        if "t.me" in text:
            processing_msg = await update.message.reply_text("⏳ جاري معالجة الرابط...")
            try:
                result = await process_telegram_link(text)
                if result.get("error"):
                    await processing_msg.edit_text(
                        f"❌ <b>خطأ:</b> <code>{result['error']}</code>",
                        parse_mode=ParseMode.HTML
                    )
                else:
                    file_path = result.get("file_path")
                    file_size = os.path.getsize(file_path) if file_path else 0
                    if file_size > MAX_FILE_SIZE:
                        await processing_msg.edit_text("⚠️ الملف أكبر من 50 ميجا ولا يمكن إرساله عبر البوت.")
                        return
                    caption = (
                        f"✅ <b>تم التحميل بواسطة Sown</b>\n"
                        f"🔗 <code>{text}</code>\n\n"
                        f"👨‍💻 <b>المطور:</b> Tariq\n"
                        f"📞 <b>واتساب:</b> +201019667530\n"
                        f"<i>تذكير: استخدام المحتوى في معصية الله حرام، وسيحاسبك الله.</i>"
                    )
                    with open(file_path, "rb") as f:
                        await update.message.reply_video(
                            video=f,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("📞 واتساب المطور", url="https://wa.me/201019667530")]
                            ])
                        )
                    # حذف الملف بعد الإرسال لتوفير المساحة
                    Path(file_path).unlink(missing_ok=True)
                    await processing_msg.delete()
            except Exception as e:
                logger.error(f"Error downloading: {e}")
                await processing_msg.edit_text(
                    f"❌ <b>فشل في التحميل:</b> <code>{str(e)}</code>",
                    parse_mode=ParseMode.HTML
                )
        else:
            await update.message.reply_text("⚠️ يرجى إرسال رابط تيليجرام فقط.")
    else:
        await update.message.reply_text(
            "🔗 من فضلك أرسل رابط فيديو أو ستوري من تيليجرام.",
            reply_markup=main_menu_keyboard()
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Sown Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
