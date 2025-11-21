from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import db
import logging

logger = logging.getLogger(__name__)

BROADCAST_MSG, EDIT_BATCHES = range(2)

async def owner_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    owner_id = int(context.bot_data.get('OWNER_ID'))
    
    if uid != owner_id:
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data="owner_stats")],
        [
            InlineKeyboardButton("👥 Active Users", callback_data="owner_active"),
            InlineKeyboardButton("🚫 Banned Users", callback_data="owner_banned")
        ],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="owner_broadcast")],
        [
            InlineKeyboardButton("🚫 Ban User", callback_data="owner_ban"),
            InlineKeyboardButton("✅ Unban User", callback_data="owner_unban")
        ],
        [InlineKeyboardButton("📚 Edit Paid Batches", callback_data="edit_batches")],
        [InlineKeyboardButton("💳 Pending Payments", callback_data="owner_payments")]
    ]
    
    owner_name = context.bot_data.get('OWNER_NAME', 'Owner')
    text = f"""
👑 Owner Panel - {owner_name}
━━━━━━━━━━━━━━━━
Full control access
"""
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def owner_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    all_users = db.get_all_users()
    active = db.get_active_users()
    banned = db.get_banned_users()
    pending = db.get_pending_payments()
    clones = db.data['cloned_bots']
    
    text = f"""
📊 Bot Statistics
━━━━━━━━━━━━━━━━
👥 Total Users: {len(all_users)}
✅ Active: {len(active)}
🚫 Banned: {len(banned)}
💳 Pending Payments: {len(pending)}
🤖 Active Clones: {sum(1 for c in clones.values() if c.get('active', False))}

📋 Fixed Plans:
• 1 Day - ₹2
• 7 Days - ₹12
• 15 Days - ₹18
• 30 Days - ₹25
"""
    
    await query.message.reply_text(text)

async def owner_active_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    active = db.get_active_users()
    
    if not active:
        await query.message.reply_text("No active users.")
        return
    
    text = f"✅ Active Users ({len(active)})\n━━━━━━━━━━━━━━━━\n\n"
    
    keyboard = []
    for uid, user in list(active.items())[:50]:
        name = user['name']
        username = user.get('username', 'None')
        button_text = f"{name} (@{username})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"userinfo_{uid}")])
    
    if len(active) > 50:
        text += "Showing first 50 users\n"
    
    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def owner_banned_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    banned = db.get_banned_users()
    
    if not banned:
        await query.message.reply_text("No banned users.")
        return
    
    text = f"🚫 Banned Users ({len(banned)})\n━━━━━━━━━━━━━━━━\n\n"
    
    keyboard = []
    for uid, user in banned.items():
        name = user['name']
        username = user.get('username', 'None')
        button_text = f"{name} (@{username})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"userinfo_{uid}")])
    
    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def user_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.data.split('_')[1]
    
    user = db.get_user(int(uid))
    if not user:
        await query.answer("User not found", show_alert=True)
        return
    
    await query.answer()
    
    is_banned = db.is_banned(int(uid))
    status = "🚫 Banned" if is_banned else "✅ Active"
    
    text = f"""
👤 User Info
━━━━━━━━━━━━━━━━
Name: {user['name']}
Username: @{user.get('username', 'None')}
ID: <code>{user['id']}</code>
Status: {status}
Joined: {user['joined'][:10]}
"""
    
    keyboard = []
    if is_banned:
        keyboard.append([InlineKeyboardButton("✅ Unban", callback_data=f"unban_{uid}")])
    else:
        keyboard.append([InlineKeyboardButton("🚫 Ban", callback_data=f"ban_{uid}")])
    
    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

async def ban_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = int(query.data.split('_')[1])
    
    db.ban_user(uid)
    await query.answer("✅ User banned!", show_alert=True)
    
    user = db.get_user(uid)
    await query.message.edit_text(f"✅ User {user['name']} ({uid}) banned.")
    logger.info(f"�� User {uid} banned")

async def unban_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = int(query.data.split('_')[1])
    
    db.unban_user(uid)
    await query.answer("✅ User unbanned!", show_alert=True)
    
    user = db.get_user(uid)
    await query.message.edit_text(f"✅ User {user['name']} ({uid}) unbanned.")
    logger.info(f"✅ User {uid} unbanned")

async def owner_ban_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        "🚫 Ban User\n━━━━━━━━━━━━━━━━\n\n"
        "Send user ID to ban:"
    )
    context.user_data['awaiting_ban'] = True

async def owner_unban_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        "✅ Unban User\n━━━━━━━━━━━━━━━━\n\n"
        "Send user ID to unban:"
    )
    context.user_data['awaiting_unban'] = True

async def owner_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        "📢 Broadcast Mode\n━━━━━━━━━━━━━━━━\n\n"
        "Send your message now.\n\n"
        "Formats:\n• Text\n• Photos\n• Videos\n• Documents\n• Voice\n\n"
        "/cancel to stop"
    )
    return BROADCAST_MSG

async def receive_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    users = db.get_active_users()
    
    total = len(users)
    status = await msg.reply_text(f"📤 Broadcasting to {total} users...")
    
    success = 0
    failed = 0
    
    for uid in users.keys():
        try:
            if msg.text:
                await context.bot.send_message(int(uid), msg.text)
            elif msg.photo:
                await context.bot.send_photo(int(uid), msg.photo[-1].file_id, caption=msg.caption or "")
            elif msg.video:
                await context.bot.send_video(int(uid), msg.video.file_id, caption=msg.caption or "")
            elif msg.document:
                await context.bot.send_document(int(uid), msg.document.file_id, caption=msg.caption or "")
            elif msg.voice:
                await context.bot.send_voice(int(uid), msg.voice.file_id)
            elif msg.audio:
                await context.bot.send_audio(int(uid), msg.audio.file_id, caption=msg.caption or "")
            success += 1
        except:
            failed += 1
    
    await status.edit_text(
        f"✅ Broadcast Complete!\n\n"
        f"✅ Sent: {success}\n"
        f"❌ Failed: {failed}"
    )
    
    logger.info(f"📢 Broadcast: {success} sent, {failed} failed")
    return ConversationHandler.END

async def edit_batches_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    current = db.get_paid_batches()
    
    await query.message.reply_text(
        f"📚 Edit Paid Batches List\n━━━━━━━━━━━━━━━━\n\n"
        f"Current text:\n{current}\n\n"
        f"Send new text now.\n"
        f"/cancel to stop"
    )
    return EDIT_BATCHES

async def receive_batches_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    db.set_paid_batches(text)
    
    await update.message.reply_text(
        f"✅ Paid Batches List Updated!\n\n"
        f"New text:\n{text}"
    )
    
    logger.info("📚 Paid batches list updated")
    return ConversationHandler.END

async def owner_payments_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    pending = db.get_pending_payments()
    
    if not pending:
        await query.message.reply_text("💳 No pending payments.")
        return
    
    await query.message.reply_text(f"💳 {len(pending)} pending payment(s):")
    
    for p in pending:
        user = db.get_user(p['user_id'])
        text = f"""
💳 Payment #{p['id']}
━━━━━━━━━━━━━━━━
👤 User: {user['name'] if user else 'Unknown'}
🆔 ID: <code>{p['user_id']}</code>
📱 @{user.get('username', 'None') if user else 'None'}

📦 Plan: {p['plan_days']} days
💰 Amount: ₹{p['plan_price']}
"""
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{p['id']}_{p['user_id']}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{p['id']}_{p['user_id']}")
            ]
        ]
        
        await context.bot.send_photo(
            query.message.chat_id,
            p['screenshot'],
            caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled. Use /start")
    return ConversationHandler.END
