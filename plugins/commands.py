import os
import logging
import asyncio
import sys
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ParseMode
from info import START_MSG, CHANNELS, ADMINS, INVITE_MSG, HELP_MSG
from utils import Media
from utils.broadcast.adduser import AddUserToDatabase
from utils.broadcast.access import db

logger = logging.getLogger(__name__)


@Client.on_message(filters.command('start'))
async def start(bot, message):
    """Start command handler"""
    await AddUserToDatabase(bot, message)
    if len(message.command) > 1 and message.command[1] == 'subscribe':
        await message.reply(INVITE_MSG, parse_mode=ParseMode.MARKDOWN)
    elif len(message.command) > 1 and message.command[1] == 'banned':
        await message.reply("Sorry, You are Banned to use me.", parse_mode=ParseMode.MARKDOWN)
    else:
        buttons = [[
            InlineKeyboardButton('Go Inline', switch_inline_query=''),
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(START_MSG, reply_markup=reply_markup)


@Client.on_message(filters.command('help'))
async def help_m(bot, message):
    await message.reply(HELP_MSG, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
    """Send basic information of channel"""
    if isinstance(CHANNELS, (int, str)):
        channels = [CHANNELS]
    elif isinstance(CHANNELS, list):
        channels = CHANNELS
    else:
        raise ValueError("Unexpected type of CHANNELS")

    text = '📑 **Indexed channels/groups**\n'

    for channel in channels:
        try:
            # Ensure correct type
            if str(channel).startswith("-100"):
                channel = int(channel)

            chat = await bot.get_chat(channel)

            if chat.username:
                text += '\n@' + chat.username
            else:
                text += '\n' + (chat.title or chat.first_name)
        except Exception as e:
            text += f"\n⚠️ Could not fetch info for `{channel}`: {e}"

    text += f'\n\n**Total:** {len(channels)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)
        


@Client.on_message(filters.command('total') & filters.user(ADMINS))
async def total(bot, message):
    """Show total files in database"""
    msg = await message.reply("Processing...⏳", quote=True)
    try:
        total = await Media.count_documents()
        await msg.edit(f'📁 Saved files: {total}')
    except Exception as e:
        logger.exception('Failed to check total files')
        await msg.edit(f'Error: {e}')


@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('logs.txt')
    except Exception as e:
        await message.reply(str(e))


@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database"""
    reply = message.reply_to_message
    if not (reply and reply.media):
        await message.reply('Reply to file with /delete which you want to delete', quote=True)
        return

    msg = await message.reply("Processing...⏳", quote=True)

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media:
            media.file_type = file_type
            break
    else:
        await msg.edit('This is not supported file format')
        return

    result = await Media.collection.delete_one({
        'file_name': media.file_name,
        'file_size': media.file_size,
        'file_type': media.file_type,
        'mime_type': media.mime_type
    })

    if result.deleted_count:
        await msg.edit('File is successfully deleted from database')
    else:
        await msg.edit('File not found in database')


@Client.on_message(filters.command(["restart"]) & filters.user(ADMINS))
async def restart(bot, update):
    logger.warning("Restarting bot using /restart command")
    msg = await update.reply_text(
        text="__Restarting.....__"
    )
    await asyncio.sleep(5)
    await msg.edit("__Bot restarted !__")
    os.execv(sys.executable, ['python3', 'bot.py'] + sys.argv)


@Client.on_callback_query(filters.regex(r"^cancel_s$"))
async def cancel_search(bot, query):
    user_id = query.from_user.id
    await bot.stop_listening(chat_id=user_id)
    await query.message.edit_text("Operation cancelled, please use /index again")


@Client.on_message(filters.command('ban') & filters.user(ADMINS))
async def ban_user(bot, message):
    command = message.text
    parts = command.split()
    if len(parts) == 2:
        user_id = int(parts[1])
        if not await db.is_user_banned(user_id):
            await db.update_ban(user_id)
        await db.ban_user(user_id)
        await message.reply(f"User `{user_id}` banned successfully.")
    else:
        await message.reply("Invalid command. Please use the format '/ban <user_id>'.")


@Client.on_message(filters.command('unban') & filters.user(ADMINS))
async def unban_user(bot, message):
    command = message.text
    parts = command.split()
    if len(parts) == 2:
        user_id = int(parts[1])
        if not await db.is_user_banned(user_id):
            await message.reply(f"User `{user_id}` is not banned yet.")
            return
        await db.unban_user(user_id)
        await message.reply(f"User `{user_id}` unbanned successfully.")
    else:
        await message.reply("Invalid command. Please use the format '/unban <user_id>'.")
