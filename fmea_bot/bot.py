"""
=============================================================
  FREE MONEY EARNING ADDA (FMEA) BOT
  Main Bot File - Professional Version 2.0
=============================================================
  Created by: FMEA Team
  Admin: @amanjee7568
=============================================================
"""

import logging
import asyncio
from datetime import datetime, timedelta
import pytz

from telegram import Update, Bot
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ChatMemberHandler, filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode
from telegram.error import TelegramError

from config import *
from database import *
from keyboards import *
from messages import *

# ── LOGGING SETUP ─────────────────────────────────────────────
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('fmea_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ── CONVERSATION STATES ───────────────────────────────────────
(BROADCAST_MSG, SCHEDULE_CONTENT, SCHEDULE_TIME, CHANNEL_POST,
 QUICK_POST, ADD_CONTENT_TITLE, ADD_CONTENT_TEXT, BLOCK_USER_ID,
 CUSTOM_TIME_INPUT) = range(9)

IST = pytz.timezone(TIMEZONE)


FAQ_RESPONSES = {
    "how to earn": "Start with freelancing, affiliate, and skill-based methods. Avoid guaranteed-income scams.",
    "is it free": "Yes, bot usage is free. We only share guidance and verified opportunities.",
    "referral": "Use menu > Refer & Earn to get your referral link and points.",
    "withdraw": "This bot shares earning guidance. It does not hold money/wallet balances.",
}



async def _on_startup(app: Application) -> None:
    """Ensure long-polling can start by removing any existing webhook."""
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Existing webhook cleared before polling startup")
    except Exception as e:
        logger.warning(f"Unable to clear webhook before startup: {e}")

# ── HELPER FUNCTIONS ──────────────────────────────────────────

def is_admin(user_id: int, username: str | None = None) -> bool:
    if user_id in ADMIN_IDS:
        return True
    if username and username.lower() in ADMIN_USERNAMES:
        return True
    return False

async def check_membership(bot: Bot, user_id: int) -> bool:
    """Check if user has joined the channel"""
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status not in ['left', 'kicked']
    except:
        return False

async def check_group_membership(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(GROUP_USERNAME, user_id)
        return member.status not in ['left', 'kicked']
    except:
        return False

async def _onboarding_status(bot: Bot, user_id: int) -> tuple[bool, bool]:
    in_channel = await check_membership(bot, user_id)
    in_group = await check_group_membership(bot, user_id)
    return in_channel, in_group

async def send_onboarding_notice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    in_channel, in_group = await _onboarding_status(context.bot, user.id)
    pending = []
    if not in_channel:
        pending.append("1) Channel join karo")
    if in_channel and not in_group:
        pending.append("2) Group join karo")
    if in_channel and in_group:
        pending.append("3) Bot start complete ✅")
    text = (
        "🚫 *Access Restricted*\n\n"
        "Bot use karne ke liye yeh process complete karna mandatory hai:\n"
        f"• 1) Channel: {CHANNEL_LINK}\n"
        f"• 2) Group: {GROUP_LINK}\n"
        f"• 3) Bot: {BOT_LINK}\n\n"
        f"⏳ *Pending:* {' | '.join(pending) if pending else 'None'}"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("👥 Join Group", url=GROUP_LINK)],
        [InlineKeyboardButton("🤖 Open Bot", url=BOT_LINK)],
        [InlineKeyboardButton("✅ Verify", callback_data="verify_join")],
    ])
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)

async def enforce_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if user and is_admin(user.id, user.username):
        return True
    in_channel, in_group = await _onboarding_status(context.bot, user.id)
    if in_channel and in_group:
        return True
    await send_onboarding_notice(update, context)
    return False

async def send_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask user to join channel first"""
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel Now!", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ I've Joined - Verify", callback_data="verify_join")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
⚠️ *Channel Join Required!*

💰 *Free Money Earning Adda* ke saari tips & tricks paane ke liye pehle channel join karna zaroori hai!

📢 *Channel:* {CHANNEL_LINK}

👆 Channel join karo aur phir "✅ I've Joined" button dabao!
    """
    
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

# ── START COMMAND ─────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    in_channel, in_group = await _onboarding_status(context.bot, user.id)
    if not (in_channel and in_group):
        await send_onboarding_notice(update, context)
        return
    
    # Handle referral
    referred_by = None
    if args and len(args) > 0:
        ref_code = args[0]
        referrer = get_user_by_referral(ref_code)
        if referrer and referrer['user_id'] != user.id:
            referred_by = referrer['user_id']
    
    # Add user to DB
    is_new = add_user(
        user.id, user.username, user.first_name, user.last_name, referred_by
    )
    
    update_last_active(user.id)
    
    # Add join bonus
    if is_new:
        add_points(user.id, JOIN_BONUS)
        
        # Notify referrer
        if referred_by:
            try:
                await context.bot.send_message(
                    referred_by,
                    f"🎉 *New Referral Alert!*\n\n"
                    f"👤 *{user.first_name}* ne aapka referral link use kiya!\n"
                    f"💰 *+{REFERRAL_BONUS} Points* aapke account mein add ho gaye!\n\n"
                    f"Keep sharing to earn more! 🚀",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
    
    # Welcome message
    welcome_enabled = get_setting('welcome_msg_enabled')
    
    welcome_text = WELCOME_TEXT.format(
        name=user.first_name,
        bonus=JOIN_BONUS
    )
    
    new_user_text = ""
    if is_new:
        new_user_text = f"\n🎁 *Aapko {JOIN_BONUS} Welcome Points mile!*\n"
        if referred_by:
            new_user_text += f"👥 *Referral Bonus Active!*\n"
    
    full_text = welcome_text + new_user_text
    
    await update.message.reply_text(
        full_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard(CHANNEL_LINK, SUPPORT_LINK)
    )
    
    logger.info(f"User {user.id} ({user.username}) started the bot")

# ── ADMIN COMMAND ─────────────────────────────────────────────

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin control panel - only for admins"""
    user = update.effective_user
    
    if not is_admin(user.id, user.username):
        await update.message.reply_text(
            "❌ *Access Denied!*\nAap admin nahi hain.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    stats = get_user_stats()
    broadcast_stats = get_broadcast_stats()
    
    admin_text = f"""
👑 *FMEA Admin Control Panel*
━━━━━━━━━━━━━━━━━━━━━━

📊 *Live Statistics:*
├ 👥 Total Users: *{stats['total']}*
├ ✅ Active Users: *{stats['active']}*
├ 🆕 Today's Joins: *{stats['today']}*
└ 📤 Total Broadcasts: *{broadcast_stats['total_broadcasts']}*

⏰ *Current Time:* {datetime.now(IST).strftime('%d/%m/%Y %H:%M')} IST

🟢 *Bot Status:* Running

━━━━━━━━━━━━━━━━━━━━━━
👆 Neeche se koi option select karo:
    """
    
    await update.message.reply_text(
        admin_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_main_keyboard()
    )

# ── CALLBACK QUERY HANDLER ────────────────────────────────────

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    await query.answer()
    
    data = query.data
    update_last_active(user.id)
    if data != "verify_join" and not is_admin(user.id, user.username):
        if not await enforce_onboarding(update, context):
            return
    
    # ── USER CALLBACKS ──────────────────────────
    
    if data == "main_menu":
        await query.message.edit_text(
            WELCOME_TEXT.format(name=user.first_name, bonus=JOIN_BONUS),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_keyboard(CHANNEL_LINK, SUPPORT_LINK)
        )
    
    elif data == "earning_tips":
        tip = EARNING_TIPS[0]
        await query.message.edit_text(
            tip['content'],
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_keyboard()
        )
    
    elif data == "earn_methods":
        await query.message.edit_text(
            "💡 *Earning Methods - FMEA*\n\nKoi bhi method select karo:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=earning_methods_keyboard()
        )
    
    elif data == "earn_freelancing":
        await query.message.edit_text(
            EARNING_TIPS[0]['content'],
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_keyboard()
        )
    
    elif data == "earn_trading":
        await query.message.edit_text(
            EARNING_TIPS[1]['content'],
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_keyboard()
        )
    
    elif data == "earn_affiliate":
        await query.message.edit_text(
            EARNING_TIPS[2]['content'],
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_keyboard()
        )
    
    elif data == "earn_apps":
        await query.message.edit_text(
            EARNING_TIPS[3]['content'],
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_keyboard()
        )
    
    elif data == "earn_youtube":
        await query.message.edit_text(
            HOW_EARN_FROM_YOUTUBE,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_keyboard()
        )
    
    elif data == "earn_reselling":
        await query.message.edit_text(
            RESELLING_GUIDE,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_keyboard()
        )
    
    elif data == "referral":
        db_user = get_user(user.id)
        if db_user:
            ref_link = f"https://t.me/{BOT_USERNAME.replace('@','')}?start={db_user['referral_code']}"
            ref_text = f"""
👥 *Refer & Earn Program*
━━━━━━━━━━━━━━━━━━━━━━

💰 *Har Referral = +{REFERRAL_BONUS} Points!*

📊 *Aapki Stats:*
├ 👥 Total Referrals: *{db_user['total_referrals']}*
└ 💎 Total Points: *{db_user['points']}*

🔗 *Aapka Referral Link:*
`{ref_link}`

📲 *Share karo:*
WhatsApp, Facebook, Instagram pe share karo aur Points kamao!

━━━━━━━━━━━━━━━━━━━━━━
_Tap link to copy_ 👆
            """
            await query.message.edit_text(
                ref_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=share_keyboard(f"https://t.me/{BOT_USERNAME.replace('@','')}", 
                                             db_user['referral_code'])
            )
    
    elif data == "leaderboard":
        top_users = get_top_referrers(10)
        lb_text = "🏆 *Top Referrers - FMEA Leaderboard*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        for i, u in enumerate(top_users):
            name = u['first_name'] or u['username'] or "User"
            lb_text += f"{medals[i]} *{name}* - {u['total_referrals']} referrals | {u['points']} pts\n"
        
        if not top_users:
            lb_text += "_Abhi koi data nahi hai. Pehle bano leaderboard mein!_ 🚀"
        
        lb_text += "\n━━━━━━━━━━━━━━━━━━━━━━\n💡 _Refer karo aur top par aao!_"
        
        await query.message.edit_text(
            lb_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_keyboard()
        )
    
    elif data == "my_stats":
        db_user = get_user(user.id)
        if db_user:
            joined = db_user['joined_at'][:10] if db_user['joined_at'] else "N/A"
            stats_text = f"""
📊 *Your FMEA Profile*
━━━━━━━━━━━━━━━━━━━━━━

👤 *Name:* {user.first_name}
🆔 *ID:* `{user.id}`
💎 *Points:* {db_user['points']}
👥 *Total Referrals:* {db_user['total_referrals']}
🔗 *Ref Code:* `{db_user['referral_code']}`
📅 *Joined:* {joined}

━━━━━━━━━━━━━━━━━━━━━━
💡 _Refer karo aur points kamao!_
            """
            await query.message.edit_text(
                stats_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=back_keyboard()
            )
    
    elif data == "daily_updates":
        await query.message.edit_text(
            f"📅 *Daily Updates Subscribe karo!*\n\n"
            f"🔔 Hamara channel join karo daily tips ke liye:\n"
            f"👉 {CHANNEL_LINK}\n\n"
            f"📲 Channel notifications ON karo sabse pehle update paane ke liye!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
            ])
        )
    
    elif data == "about_fmea":
        await query.message.edit_text(
            ABOUT_FMEA,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_keyboard()
        )

    elif data == "ask_question":
        context.user_data["awaiting_user_question"] = True
        await query.message.edit_text(
            "❓ *Ask Your Question*\n\nApna sawal type kijiye. Bot pehle instant answer dega; zarurat par admin ko forward hoga.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=cancel_keyboard()
        )
    
    elif data == "verify_join":
        in_channel, in_group = await _onboarding_status(context.bot, user.id)
        if in_channel and in_group:
            await query.message.edit_text(
                "✅ *Verification Successful!*\n\nChannel + Group verification complete! 🎉\n\nAb aap bot use kar sakte hain.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu_keyboard(CHANNEL_LINK, SUPPORT_LINK)
            )
        else:
            await send_onboarding_notice(update, context)
    
    # ── ADMIN CALLBACKS ──────────────────────────────────────
    
    elif data == "admin_panel":
        if not is_admin(user.id, user.username):
            await query.answer("❌ Access Denied!", show_alert=True)
            return
        
        stats = get_user_stats()
        admin_text = f"""
👑 *FMEA Admin Control Panel*
━━━━━━━━━━━━━━━━━━━━━━

📊 *Live Statistics:*
├ 👥 Total Users: *{stats['total']}*
├ ✅ Active Users: *{stats['active']}*
├ 🆕 Today's Joins: *{stats['today']}*

⏰ *Time:* {datetime.now(IST).strftime('%d/%m/%Y %H:%M')} IST
━━━━━━━━━━━━━━━━━━━━━━
        """
        await query.message.edit_text(
            admin_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_main_keyboard()
        )

    elif data == "admin_questions":
        if not is_admin(user.id, user.username):
            await query.answer("❌ Access Denied!", show_alert=True)
            return
        qs = get_open_questions(10)
        if not qs:
            await query.message.edit_text(
                "✅ *No open questions*",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
            )
        else:
            q_text = "🧾 *Open User Questions*\n\n"
            for q in qs[:10]:
                q_text += f"• #{q['id']} - user `{q['user_id']}`\n{q['question'][:80]}\n\n"
            q_text += "Reply format in chat: `/reply <id> your answer`"
            await query.message.edit_text(
                q_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
            )
    
    elif data == "admin_stats":
        if not is_admin(user.id, user.username):
            await query.answer("❌ Access Denied!", show_alert=True)
            return
        
        stats = get_user_stats()
        bc_stats = get_broadcast_stats()
        
        stats_text = f"""
📊 *Detailed Bot Statistics*
━━━━━━━━━━━━━━━━━━━━━━

👥 *User Stats:*
├ Total Users: *{stats['total']}*
├ Active Users: *{stats['active']}*
├ Blocked Users: *{stats['total'] - stats['active']}*
└ Joined Today: *{stats['today']}*

📤 *Broadcast Stats:*
└ Total Broadcasts Sent: *{bc_stats['total_broadcasts']}*

⏰ *Last Updated:* {datetime.now(IST).strftime('%d/%m/%Y %H:%M:%S')} IST

🤖 *Bot Version:* {BOT_VERSION}
        """
        await query.message.edit_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="admin_panel")
            ]])
        )
    
    elif data == "admin_settings":
        if not is_admin(user.id, user.username):
            await query.answer("❌ Access Denied!", show_alert=True)
            return
        
        auto_post = get_setting('auto_post_enabled') or 'true'
        welcome_msg = get_setting('welcome_msg_enabled') or 'true'
        referral = get_setting('referral_enabled') or 'true'
        bot_status = get_setting('bot_status') or 'active'
        
        await query.message.edit_text(
            "⚙️ *Bot Settings - Toggle On/Off*\n\nKoi bhi setting toggle karo:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_settings_keyboard(auto_post, welcome_msg, referral, bot_status)
        )
    
    elif data == "toggle_auto_post":
        if not is_admin(user.id, user.username):
            return
        current = get_setting('auto_post_enabled')
        new_val = 'false' if current == 'true' else 'true'
        set_setting('auto_post_enabled', new_val)
        await query.answer(f"✅ Auto Post: {'ON' if new_val == 'true' else 'OFF'}", show_alert=True)
        
        auto_post = get_setting('auto_post_enabled') or 'true'
        welcome_msg = get_setting('welcome_msg_enabled') or 'true'
        referral = get_setting('referral_enabled') or 'true'
        bot_status = get_setting('bot_status') or 'active'
        
        await query.message.edit_reply_markup(
            reply_markup=admin_settings_keyboard(auto_post, welcome_msg, referral, bot_status)
        )
    
    elif data == "toggle_welcome":
        if not is_admin(user.id, user.username):
            return
        current = get_setting('welcome_msg_enabled')
        new_val = 'false' if current == 'true' else 'true'
        set_setting('welcome_msg_enabled', new_val)
        await query.answer(f"✅ Welcome Message: {'ON' if new_val == 'true' else 'OFF'}", show_alert=True)
        
        auto_post = get_setting('auto_post_enabled') or 'true'
        welcome_msg = get_setting('welcome_msg_enabled') or 'true'
        referral = get_setting('referral_enabled') or 'true'
        bot_status = get_setting('bot_status') or 'active'
        await query.message.edit_reply_markup(
            reply_markup=admin_settings_keyboard(auto_post, welcome_msg, referral, bot_status)
        )
    
    elif data == "toggle_referral":
        if not is_admin(user.id, user.username):
            return
        current = get_setting('referral_enabled')
        new_val = 'false' if current == 'true' else 'true'
        set_setting('referral_enabled', new_val)
        await query.answer(f"✅ Referral: {'ON' if new_val == 'true' else 'OFF'}", show_alert=True)
        
        auto_post = get_setting('auto_post_enabled') or 'true'
        welcome_msg = get_setting('welcome_msg_enabled') or 'true'
        referral = get_setting('referral_enabled') or 'true'
        bot_status = get_setting('bot_status') or 'active'
        await query.message.edit_reply_markup(
            reply_markup=admin_settings_keyboard(auto_post, welcome_msg, referral, bot_status)
        )
    
    elif data == "admin_promo":
        if not is_admin(user.id, user.username):
            await query.answer("❌ Access Denied!", show_alert=True)
            return
        await query.message.edit_text(
            "🔥 *Auto Promotion System*\n\nKoi promotion message bhejo:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=promo_keyboard()
        )
    
    elif data.startswith("send_promo_"):
        if not is_admin(user.id, user.username):
            return
        
        promo_num = int(data.split("_")[-1]) - 1
        if promo_num < len(PROMO_MESSAGES):
            promo_msg = PROMO_MESSAGES[promo_num].format(
                channel_link=CHANNEL_LINK,
                support_link=SUPPORT_LINK
            )
            
            # Store in context for confirmation
            context.user_data['pending_broadcast'] = promo_msg
            context.user_data['pending_type'] = 'broadcast'
            
            await query.message.edit_text(
                f"📤 *Preview:*\n\n{promo_msg}\n\n━━━━━━━━━━━━━━━━\n⚠️ Ye message sabhi users ko jayega. Confirm?",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=confirm_keyboard("broadcast")
            )
    
    elif data == "send_all_promos":
        if not is_admin(user.id, user.username):
            return
        all_promos = "\n\n━━━━━\n\n".join([
            p.format(channel_link=CHANNEL_LINK, support_link=SUPPORT_LINK) 
            for p in PROMO_MESSAGES
        ])
        context.user_data['pending_broadcast'] = all_promos
        context.user_data['pending_type'] = 'broadcast'
        
        await query.message.edit_text(
            f"📤 Sabhi promotional messages send honge.\n\nConfirm karein?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=confirm_keyboard("broadcast")
        )
    
    elif data == "confirm_broadcast":
        if not is_admin(user.id, user.username):
            return
        
        message = context.user_data.get('pending_broadcast', '')
        if message:
            await query.message.edit_text(
                "⏳ *Broadcasting...* Please wait!",
                parse_mode=ParseMode.MARKDOWN
            )
            
            users = get_all_users()
            sent = 0
            failed = 0
            
            for uid in users:
                try:
                    await context.bot.send_message(
                        uid,
                        message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    sent += 1
                    await asyncio.sleep(0.05)  # Rate limit protection
                except Exception as e:
                    failed += 1
            
            log_broadcast(message, sent, failed, user.id)
            
            await query.message.edit_text(
                f"✅ *Broadcast Complete!*\n\n"
                f"📤 Sent: *{sent}*\n"
                f"❌ Failed: *{failed}*\n"
                f"📊 Total: *{sent + failed}*",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")
                ]])
            )
    
    elif data == "admin_users":
        if not is_admin(user.id, user.username):
            await query.answer("❌ Access Denied!", show_alert=True)
            return
        
        await query.message.edit_text(
            "👥 *User Management*\n\nKoi option select karo:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_users_keyboard()
        )
    
    elif data == "users_total":
        if not is_admin(user.id, user.username):
            return
        stats = get_user_stats()
        await query.answer(
            f"👥 Total: {stats['total']} | Active: {stats['active']} | Today: {stats['today']}",
            show_alert=True
        )
    
    elif data == "users_top":
        if not is_admin(user.id, user.username):
            return
        top_users = get_top_referrers(10)
        text = "🏆 *Top 10 Referrers:*\n\n"
        for i, u in enumerate(top_users, 1):
            name = u['first_name'] or "User"
            text += f"{i}. {name} - {u['total_referrals']} refs\n"
        
        await query.message.edit_text(
            text or "No data yet",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="admin_users")
            ]])
        )
    
    elif data == "users_export":
        if not is_admin(user.id, user.username):
            return
        users = get_all_users(exclude_blocked=False)
        export_text = f"📊 FMEA User Export\nTotal: {len(users)}\n\nUser IDs:\n"
        export_text += "\n".join([str(u) for u in users[:100]])
        if len(users) > 100:
            export_text += f"\n... and {len(users)-100} more"
        
        await context.bot.send_message(
            user.id,
            f"```\n{export_text}\n```",
            parse_mode=ParseMode.MARKDOWN
        )
        await query.answer("✅ Export sent to your DM!", show_alert=True)
    
    elif data == "admin_view_posts":
        if not is_admin(user.id, user.username):
            return
        posts = get_all_scheduled_posts()
        
        if not posts:
            text = "📋 *Scheduled Posts*\n\nAbhi koi scheduled post nahi hai."
        else:
            text = "📋 *Recent Scheduled Posts:*\n\n"
            for p in posts[:5]:
                status_icon = "⏳" if p['status'] == 'pending' else "✅"
                text += f"{status_icon} ID:{p['id']} - {p['schedule_time']} - {p['status']}\n"
                text += f"   _{p['content'][:50]}..._\n\n"
        
        await query.message.edit_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="admin_panel")
            ]])
        )
    
    elif data == "admin_schedule":
        if not is_admin(user.id, user.username):
            return
        await query.message.edit_text(
            "📅 *Schedule Post to Channel*\n\nPehle time select karo:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=schedule_time_keyboard()
        )
    
    elif data.startswith("sched_"):
        if not is_admin(user.id, user.username):
            return
        time_val = data.replace("sched_", "")
        if time_val != "custom":
            context.user_data['schedule_time'] = time_val
            context.user_data['awaiting_schedule_content'] = True
            await query.message.edit_text(
                f"📅 *Time Set: {time_val} IST*\n\n"
                f"Ab apna post content type karo:\n"
                f"_(Text, ya koi bhi message)_",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=cancel_keyboard()
            )
        else:
            context.user_data['awaiting_custom_time'] = True
            await query.message.edit_text(
                "⏰ Custom time type karo (Format: HH:MM, e.g., 18:30):",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=cancel_keyboard()
            )
    
    elif data == "admin_broadcast":
        if not is_admin(user.id, user.username):
            return
        context.user_data['awaiting_broadcast'] = True
        await query.message.edit_text(
            "📤 *Broadcast Message*\n\n"
            "Woh message type karo jo aap sabhi users ko bhejna chahte ho:\n\n"
            "_(Markdown formatting support hai: *bold*, _italic_, `code`)_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=cancel_keyboard()
        )
    
    elif data == "admin_channel_post":
        if not is_admin(user.id, user.username):
            return
        context.user_data['awaiting_channel_post'] = True
        await query.message.edit_text(
            "📢 *Post to Channel*\n\n"
            "Channel mein post karne ke liye message type karo:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=cancel_keyboard()
        )
    
    elif data == "admin_quick_post":
        if not is_admin(user.id, user.username):
            return
        context.user_data['awaiting_quick_post'] = True
        await query.message.edit_text(
            "💡 *Quick Post*\n\n"
            "Apna message type karo (channel + all users mein jayega):",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=cancel_keyboard()
        )
    
    elif data == "admin_content":
        if not is_admin(user.id, user.username):
            return
        content_list = get_content_list()
        
        text = f"📚 *Content Library*\n\nTotal: {len(content_list)} items\n\n"
        for c in content_list[:5]:
            text += f"📌 *{c['title']}* ({c['category']})\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Add Content", callback_data="add_content")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
        ]
        
        await query.message.edit_text(
            text or "No content yet",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data == "add_content":
        if not is_admin(user.id, user.username):
            return
        context.user_data['awaiting_content_title'] = True
        await query.message.edit_text(
            "📝 *Add New Content*\n\nContent ka title type karo:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=cancel_keyboard()
        )


# ── MESSAGE HANDLER ───────────────────────────────────────────

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    if message is None:
        return
    text = message.text if message.text else ""

    if message.chat.type == "channel":
        return

    if message.chat.type in ("group", "supergroup"):
        if text and not text.startswith("/"):
            try:
                await message.reply_text(f"Detailed help ke liye bot open karein: {BOT_LINK}")
            except:
                pass

    # Group/channel moderation for abusive words
    if message.chat.type in ("group", "supergroup"):
        if not is_admin(user.id, user.username) and text and _contains_blocked_words(text):
            try:
                await message.delete()
            except:
                pass
            try:
                await context.bot.ban_chat_member(message.chat.id, user.id)
            except Exception as e:
                logger.warning(f"Unable to ban abusive user {user.id}: {e}")
            block_user(user.id)
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        admin_id,
                        f"🚫 User blocked from group/channel context.\nUser: `{user.id}` (@{user.username})\nMessage: {text}\n\nUnblock flow: user sends /unbanrequest in bot DM, then admin uses /approveunban.",
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except:
                    pass
            return
    
    update_last_active(user.id)
    
    # Maintenance mode check
    if get_setting('maintenance_mode') == 'true' and not is_admin(user.id, user.username):
        await message.reply_text(
            "🔧 *Maintenance Mode Active*\n\n"
            "Bot abhi maintenance pe hai. Thodi der baad try karo.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Force onboarding flow only in private bot chat
    if message.chat.type == "private":
        in_channel, in_group = await _onboarding_status(context.bot, user.id)
        if not (in_channel and in_group) and not is_admin(user.id, user.username):
            await send_onboarding_notice(update, context)
            return
    
    # Admin input handling
    if is_admin(user.id, user.username):
        
        # Broadcast message input
        if context.user_data.get('awaiting_broadcast'):
            context.user_data['awaiting_broadcast'] = False
            context.user_data['pending_broadcast'] = text
            context.user_data['pending_type'] = 'broadcast'
            
            await message.reply_text(
                f"📤 *Broadcast Preview:*\n\n{text}\n\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"👥 {len(get_all_users())} users ko jayega\n\nConfirm?",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=confirm_keyboard("broadcast")
            )
            return
        
        # Schedule content input
        if context.user_data.get('awaiting_schedule_content'):
            context.user_data['awaiting_schedule_content'] = False
            schedule_time = context.user_data.get('schedule_time', '12:00')
            
            # Create scheduled post
            post_id = add_scheduled_post(
                content=text,
                schedule_time=schedule_time,
                created_by=user.id
            )
            
            await message.reply_text(
                f"✅ *Post Scheduled Successfully!*\n\n"
                f"🆔 Post ID: {post_id}\n"
                f"⏰ Time: {schedule_time} IST\n"
                f"📝 Content: _{text[:100]}..._",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")
                ]])
            )
            return
        
        # Custom time input
        if context.user_data.get('awaiting_custom_time'):
            context.user_data['awaiting_custom_time'] = False
            context.user_data['schedule_time'] = text
            context.user_data['awaiting_schedule_content'] = True
            
            await message.reply_text(
                f"⏰ Time set: *{text}*\n\nAb content type karo:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=cancel_keyboard()
            )
            return
        
        # Channel post input
        if context.user_data.get('awaiting_channel_post'):
            context.user_data['awaiting_channel_post'] = False
            
            try:
                await context.bot.send_message(
                    CHANNEL_USERNAME,
                    text,
                    parse_mode=ParseMode.MARKDOWN
                )
                await message.reply_text(
                    "✅ *Channel pe post ho gaya!*",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")
                    ]])
                )
            except Exception as e:
                await message.reply_text(
                    f"❌ Error: {str(e)}\n\n"
                    "Make sure bot is admin in channel!",
                    parse_mode=ParseMode.MARKDOWN
                )
            return
        
        # Quick post (channel + broadcast)
        if context.user_data.get('awaiting_quick_post'):
            context.user_data['awaiting_quick_post'] = False
            
            # Post to channel
            try:
                await context.bot.send_message(
                    CHANNEL_USERNAME, text, parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                await message.reply_text(f"⚠️ Channel post failed: {e}")
            
            # Broadcast to users
            users = get_all_users()
            sent = 0
            for uid in users:
                try:
                    await context.bot.send_message(uid, text, parse_mode=ParseMode.MARKDOWN)
                    sent += 1
                    await asyncio.sleep(0.05)
                except:
                    pass
            
            await message.reply_text(
                f"✅ *Quick Post Done!*\n\n"
                f"📢 Channel: ✅\n"
                f"📤 Broadcast: {sent} users",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")
                ]])
            )
            return
        
        # Content title input
        if context.user_data.get('awaiting_content_title'):
            context.user_data['awaiting_content_title'] = False
            context.user_data['content_title'] = text
            context.user_data['awaiting_content_text'] = True
            
            await message.reply_text(
                f"📝 Title: *{text}*\n\nAb content/body type karo:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=cancel_keyboard()
            )
            return
        
        # Content body input
        if context.user_data.get('awaiting_content_text'):
            context.user_data['awaiting_content_text'] = False
            title = context.user_data.get('content_title', 'Untitled')
            
            content_id = add_content(title, text, added_by=user.id)
            
            await message.reply_text(
                f"✅ *Content Added!*\n\n"
                f"🆔 ID: {content_id}\n"
                f"📌 Title: {title}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")
                ]])
            )
            return
    
    # User question mode
    if context.user_data.get('awaiting_user_question'):
        context.user_data['awaiting_user_question'] = False
        low = text.lower()
        answer = None
        for k, v in FAQ_RESPONSES.items():
            if k in low:
                answer = v
                break

        if answer:
            await message.reply_text(
                f"✅ *Quick Answer:*\n{answer}\n\nNeed more help? Tap Ask Question again.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu_keyboard(CHANNEL_LINK, SUPPORT_LINK)
            )
        else:
            qid = add_user_question(user.id, user.username, text)
            await message.reply_text(
                f"🧾 Aapka question admin queue mein add ho gaya (ID: *{qid}*).\nHum genuine answer ke saath jaldi reply karenge.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu_keyboard(CHANNEL_LINK, SUPPORT_LINK)
            )
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(admin_id, f"🆕 User Question #{qid}\nUser: `{user.id}` (@{user.username})\nQ: {text}", parse_mode=ParseMode.MARKDOWN)
                except:
                    pass
        return

    # Regular user: try quick answer first in private chat
    if message.chat.type == "private" and text:
        low = text.lower()
        for k, v in FAQ_RESPONSES.items():
            if k in low:
                await message.reply_text(
                    f"✅ *Quick Answer:*\n{v}",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=main_menu_keyboard(CHANNEL_LINK, SUPPORT_LINK)
                )
                return
    await message.reply_text(
        "👋 *Kya chahiye aapko?*\n\nNeeche se option choose karo:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard(CHANNEL_LINK, SUPPORT_LINK)
    )

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await enforce_onboarding(update, context):
        return
    context.user_data['awaiting_user_question'] = True
    await update.message.reply_text(
        "❓ Apna question type kijiye. Genuine jawab diya jayega; complex case admin ko forward hoga.",
        parse_mode=ParseMode.MARKDOWN
    )

async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id, user.username):
        await update.message.reply_text("❌ Access denied")
        return
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: /reply <question_id> <message>")
        return
    try:
        qid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid question id")
        return
    reply_text = " ".join(context.args[1:])
    q = {item['id']: item for item in get_open_questions(200)}.get(qid)
    if not q:
        await update.message.reply_text("Question not found/open")
        return
    await context.bot.send_message(q['user_id'], f"📩 *Admin Reply*\n\n{reply_text}", parse_mode=ParseMode.MARKDOWN)
    close_user_question(qid, reply_text)
    await update.message.reply_text(f"✅ Replied to question #{qid}")

async def setwelcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id, user.username):
        await update.message.reply_text("❌ Access denied")
        return
    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text("Usage: /setwelcome <welcome text with {name}>")
        return
    set_setting("channel_welcome_text", text)
    await update.message.reply_text("✅ Channel welcome text updated.")

async def setfeatures_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id, user.username):
        await update.message.reply_text("❌ Access denied")
        return
    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text("Usage: /setfeatures <features text>")
        return
    set_setting("channel_features_text", text)
    await update.message.reply_text("✅ Channel features text updated.")

async def setbadwords_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id, user.username):
        await update.message.reply_text("❌ Access denied")
        return
    words = " ".join(context.args).strip().lower()
    if not words:
        await update.message.reply_text("Usage: /setbadwords word1,word2,word3")
        return
    set_setting("blocked_words", words)
    await update.message.reply_text("✅ Blocked words list updated.")

async def unban_request_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reason = " ".join(context.args).strip()
    if not reason:
        await update.message.reply_text("Usage: /unbanrequest <clear reason in DM>")
        return
    request_id = add_unban_request(user.id, user.username, reason)
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, f"🆕 Unban request #{request_id}\nUser: `{user.id}` (@{user.username})\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    await update.message.reply_text(f"✅ Unban request submitted. Request ID: {request_id}")

async def review_unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id, user.username):
        await update.message.reply_text("❌ Access denied")
        return
    pending = get_pending_unban_requests(20)
    if not pending:
        await update.message.reply_text("No pending unban requests.")
        return
    lines = ["🧾 Pending unban requests:"]
    for item in pending:
        lines.append(f"#{item['id']} | user {item['user_id']} (@{item['username']})")
        lines.append(f"Reason: {item['reason']}")
    lines.append("\nApprove with: /approveunban <request_id>")
    await update.message.reply_text("\n".join(lines))

async def approve_unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id, user.username):
        await update.message.reply_text("❌ Access denied")
        return
    if not context.args:
        await update.message.reply_text("Usage: /approveunban <request_id>")
        return
    try:
        request_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid request_id")
        return
    req = get_unban_request(request_id)
    if not req or req['status'] != 'pending':
        await update.message.reply_text("Request not found/pending.")
        return
    approve_unban_request(request_id, user.id)
    unblock_user(req['user_id'])
    await update.message.reply_text(f"✅ User {req['user_id']} unblocked.")

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmu = update.chat_member
    if cmu is None:
        return
    old_status = cmu.old_chat_member.status
    new_status = cmu.new_chat_member.status
    if old_status in ("left", "kicked") and new_status in ("member", "restricted"):
        user = cmu.new_chat_member.user
        welcome_text = (get_setting("channel_welcome_text") or "🎉 Welcome {name}!").format(name=user.first_name)
        features_text = get_setting("channel_features_text") or ""
        final_text = (
            f"{welcome_text}\n\n"
            f"{features_text}\n\n"
            f"👥 Pehle group me active rahiye, phir bot use karein:\n{BOT_LINK}\n\n"
            "💬 Genuine demand ke liye /ask use karein."
        )
        try:
            await context.bot.send_message(chat_id=cmu.chat.id, text=final_text, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.warning(f"Failed to send welcome message in chat {cmu.chat.id}: {e}")

def _contains_blocked_words(text: str) -> bool:
    blocked = (get_setting("blocked_words") or "").lower().split(",")
    low = text.lower()
    return any(word.strip() and word.strip() in low for word in blocked)

# ── HELP COMMAND ──────────────────────────────────────────────

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id, user.username):
        if not await enforce_onboarding(update, context):
            return
    
    if is_admin(user.id, user.username):
        help_text = """
👑 *FMEA Admin Commands:*

/admin - Open Admin Control Panel
/broadcast - Broadcast to all users
/post - Post to channel
/stats - View statistics
/settings - Bot settings
/help - Show this help
/setwelcome - Set channel welcome text
/setfeatures - Set channel features text
/setbadwords - Set abusive words list
/reviewunban - View unban requests
/approveunban - Approve unban request

📌 *Admin Features:*
├ 📤 Broadcast messages
├ 📅 Schedule posts
├ 📢 Channel posting
├ 👥 User management
├ 📊 Analytics
└ ⚙️ Settings control
        """
    else:
        help_text = """
💰 *FMEA Bot Commands:*

/start - Start the bot
/menu - Show main menu
/tips - Earning tips
/referral - Your referral link
/stats - Your stats
/help - Help
/unbanrequest - Request unblock with reason

📌 *Features:*
├ 💸 Daily earning tips
├ 🎯 Money making methods
├ 👥 Refer & earn
└ 📊 Leaderboard
        """
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard(CHANNEL_LINK, SUPPORT_LINK)
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await enforce_onboarding(update, context):
        return
    await update.message.reply_text(
        f"💰 *Free Money Earning Adda*\n\nMain Menu:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard(CHANNEL_LINK, SUPPORT_LINK)
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id, user.username):
        if not await enforce_onboarding(update, context):
            return
    
    if is_admin(user.id, user.username):
        stats = get_user_stats()
        await update.message.reply_text(
            f"📊 *Bot Statistics:*\n\n"
            f"👥 Total Users: {stats['total']}\n"
            f"✅ Active: {stats['active']}\n"
            f"🆕 Today: {stats['today']}",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        db_user = get_user(user.id)
        if db_user:
            await update.message.reply_text(
                f"📊 *Your Stats:*\n\n"
                f"💎 Points: {db_user['points']}\n"
                f"👥 Referrals: {db_user['total_referrals']}",
                parse_mode=ParseMode.MARKDOWN
            )

# ── AUTO POST SCHEDULER ───────────────────────────────────────

async def send_daily_update(context: ContextTypes.DEFAULT_TYPE):
    """Automatically send daily update to channel"""
    auto_post_enabled = get_setting('auto_post_enabled')
    if auto_post_enabled != 'true':
        return
    
    now = datetime.now(IST)
    
    # Try to get content from library first
    content = get_random_content()
    
    if content:
        post_text = DAILY_UPDATE_TEMPLATE.format(
            date=now.strftime('%d %B %Y'),
            time=now.strftime('%H:%M'),
            content=content['content']
        )
    else:
        # Use default earning tips
        import random
        tip = random.choice(EARNING_TIPS)
        post_text = DAILY_UPDATE_TEMPLATE.format(
            date=now.strftime('%d %B %Y'),
            time=now.strftime('%H:%M'),
            content=tip['content']
        )
    
    try:
        await context.bot.send_message(
            CHANNEL_USERNAME,
            post_text,
            parse_mode=ParseMode.MARKDOWN
        )
        logger.info(f"Daily update sent to channel at {now}")
        
        # Update counter
        current_count = int(get_setting('total_posts_sent') or '0')
        set_setting('total_posts_sent', str(current_count + 1))
        
    except Exception as e:
        logger.error(f"Failed to send daily update: {e}")

async def check_scheduled_posts(context: ContextTypes.DEFAULT_TYPE):
    """Check and send scheduled posts"""
    posts = get_pending_posts()
    now = datetime.now(IST)
    current_time = now.strftime('%H:%M')
    
    for post in posts:
        if post['schedule_time'] == current_time:
            try:
                await context.bot.send_message(
                    CHANNEL_USERNAME,
                    post['content'],
                    parse_mode=ParseMode.MARKDOWN
                )
                mark_post_sent(post['id'])
                logger.info(f"Scheduled post {post['id']} sent to channel")
            except Exception as e:
                logger.error(f"Failed to send scheduled post {post['id']}: {e}")

async def send_daily_promo(context: ContextTypes.DEFAULT_TYPE):
    """Send daily promotion to all users"""
    auto_post = get_setting('auto_post_enabled')
    if auto_post != 'true':
        return
    
    import random
    promo = random.choice(PROMO_MESSAGES).format(
        channel_link=CHANNEL_LINK,
        support_link=SUPPORT_LINK
    )
    
    users = get_all_users()
    sent = 0
    for uid in users:
        try:
            await context.bot.send_message(uid, promo, parse_mode=ParseMode.MARKDOWN)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            pass
    
    logger.info(f"Daily promo sent to {sent} users")

# ── ERROR HANDLER ─────────────────────────────────────────────

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")
    
    if isinstance(context.error, TelegramError):
        logger.error(f"Telegram Error: {context.error}")

# ── MAIN FUNCTION ─────────────────────────────────────────────

def main():
    """Start the FMEA Bot"""
    print("=" * 60)
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing. Set it as environment variable before running bot.")

    print("  🚀 FREE MONEY EARNING ADDA BOT - Starting...")
    print("=" * 60)
    
    # Initialize database
    init_database()
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).post_init(_on_startup).build()
    
    # ── Register Handlers ──────────────────────────────────────
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("ask", ask_command))
    app.add_handler(CommandHandler("reply", reply_command))
    app.add_handler(CommandHandler("setwelcome", setwelcome_command))
    app.add_handler(CommandHandler("setfeatures", setfeatures_command))
    app.add_handler(CommandHandler("setbadwords", setbadwords_command))
    app.add_handler(CommandHandler("unbanrequest", unban_request_command))
    app.add_handler(CommandHandler("reviewunban", review_unban_command))
    app.add_handler(CommandHandler("approveunban", approve_unban_command))
    
    # Callback query handler
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(ChatMemberHandler(welcome_new_member, ChatMemberHandler.CHAT_MEMBER))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    # ── Job Scheduler ──────────────────────────────────────────
    job_queue = app.job_queue
    
    # Daily updates at 9 AM, 2 PM, 8 PM IST
    for time_str in AUTO_POST_TIMES:
        hour, minute = map(int, time_str.split(':'))
        job_queue.run_daily(
            send_daily_update,
            time=datetime.now(IST).replace(hour=hour, minute=minute, second=0, microsecond=0).timetz(),
        )
    
    # Check scheduled posts every minute
    job_queue.run_repeating(check_scheduled_posts, interval=60, first=10)
    
    # Daily promo at 7 PM IST
    job_queue.run_daily(
        send_daily_promo,
        time=datetime.now(IST).replace(hour=19, minute=0, second=0, microsecond=0).timetz(),
    )
    
    print("✅ Bot started successfully!")
    print(f"📊 Admin IDs: {ADMIN_IDS}")
    print(f"📢 Channel: {CHANNEL_USERNAME}")
    print(f"⏰ Auto posts: {AUTO_POST_TIMES}")
    print("=" * 60)
    print("🤖 Bot is running... Press Ctrl+C to stop")
    print("=" * 60)
    
    # Run the bot
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        stop_signals=None
    )

if __name__ == "__main__":
    main()
