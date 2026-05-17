#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محرك تحميل فيديوهات وستوريات تيليجرام باستخدام Telethon
يستخدم بيانات API التالية:
    API_ID = 35058015
    API_HASH = 725d636e85cb210b3a336583bb5cede2
"""
import os
import asyncio
import tempfile
import re
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto, DocumentAttributeVideo, PeerUser, PeerChannel

# الإعدادات
API_ID = 35058015
API_HASH = "725d636e85cb210b3a336583bb5cede2"
SESSION_STRING = os.getenv("TELETHON_SESSION")  # يجب تعيين جلسة المستخدم

def parse_telegram_link(link: str):
    """تحليل رابط تيليجرام لاستخراج نوعه (منشور أو حساب)"""
    link = link.strip()
    pattern_post = r"https?://t\.me/([^/]+)/(\d+)(?:\?.*)?$"
    pattern_account = r"https?://t\.me/([^/]+)/?$"
    m = re.match(pattern_post, link)
    if m:
        return {"type": "post", "username": m.group(1), "message_id": int(m.group(2))}
    m = re.match(pattern_account, link)
    if m:
        return {"type": "account", "username": m.group(1)}
    return None

async def process_telegram_link(link: str):
    """معالجة رابط وإرجاع مسار الملف المحمل أو خطأ"""
    if not SESSION_STRING:
        return {"error": "جلسة Telethon غير مضبوطة. تأكد من تعيين TELETHON_SESSION"}

    parsed = parse_telegram_link(link)
    if not parsed:
        return {"error": "الرابط غير مدعوم. تأكد من إرسال رابط منشور أو رابط حساب صحيح"}

    # إنشاء عميل Telethon
    client = TelegramClient(
        StringSession(SESSION_STRING), API_ID, API_HASH,
        device_model="SownBot", system_version="1.0"
    )

    try:
        await client.connect()
        if not await client.is_user_authorized():
            return {"error": "انتهت صلاحية الجلسة. أعد توليدها"}

        file_path = None
        if parsed["type"] == "post":
            # جلب الرسالة
            try:
                entity = await client.get_entity(parsed["username"])
            except Exception:
                return {"error": "لم يتم العثور على القناة/المجموعة. تأكد أنها عامة"}

            message = await client.get_messages(entity, ids=parsed["message_id"])
            if not message:
                return {"error": "المنشور غير موجود"}

            # استخراج الفيديو من الوسائط
            if message.media:
                if isinstance(message.media, MessageMediaDocument):
                    for attr in message.media.document.attributes:
                        if isinstance(attr, DocumentAttributeVideo):
                            file_path = await message.download_media(
                                file=tempfile.mkdtemp()
                            )
                            break
                    if not file_path:
                        # ربما صورة متحركة أو ملف آخر، نحاول التنزيل إن كان مدعوماً
                        if message.media.document.mime_type.startswith("video/"):
                            file_path = await message.download_media(
                                file=tempfile.mkdtemp()
                            )
                elif isinstance(message.media, MessageMediaPhoto):
                    return {"error": "المنشور يحتوي على صورة فقط، وليس فيديو"}
                else:
                    # محاولة تحميل أي وسائط أخرى كفيديو إذا كانت فيديو
                    file_path = await message.download_media(
                        file=tempfile.mkdtemp()
                    )
                    if file_path and not Path(file_path).suffix.lower() in ('.mp4', '.avi', '.mkv', '.mov'):
                        Path(file_path).unlink(missing_ok=True)
                        return {"error": "الملف المحمل ليس فيديو"}
            else:
                return {"error": "المنشور لا يحتوي على وسائط"}

        elif parsed["type"] == "account":
            # جلب المستخدم
            try:
                user = await client.get_entity(parsed["username"])
            except Exception:
                return {"error": "الحساب غير موجود أو غير عام"}

            # جلب الستوريز النشطة
            try:
                stories = await client.get_stories(user, limit=1)  # أحدث ستوري
            except Exception as e:
                return {"error": f"تعذر جلب الستوريز: {str(e)}"}

            if not stories or not stories[0].media:
                return {"error": "لا توجد ستوريز نشطة حالياً"}

            story = stories[0]
            # تحميل وسائط الستوري (فيديو إذا وجد)
            if hasattr(story.media, 'document'):
                for attr in story.media.document.attributes:
                    if isinstance(attr, DocumentAttributeVideo):
                        file_path = await client.download_media(
                            story, file=tempfile.mkdtemp()
                        )
                        break
                if not file_path and story.media.document.mime_type.startswith("video/"):
                    file_path = await client.download_media(
                        story, file=tempfile.mkdtemp()
                    )
            elif hasattr(story.media, 'photo'):
                return {"error": "الستوري صورة وليس فيديو"}
            else:
                file_path = await client.download_media(
                    story, file=tempfile.mkdtemp()
                )
                if file_path and not Path(file_path).suffix.lower() in ('.mp4', '.avi', '.mkv', '.mov'):
                    Path(file_path).unlink(missing_ok=True)
                    return {"error": "الستوري لا يحتوي على فيديو"}

        if file_path and os.path.exists(file_path):
            return {"file_path": file_path}
        else:
            return {"error": "فشل تحميل الملف"}

    except Exception as e:
        return {"error": f"خطأ غير متوقع: {str(e)}"}
    finally:
        await client.disconnect()
