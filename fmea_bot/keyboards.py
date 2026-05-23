"""
=============================================================
  FREE MONEY EARNING ADDA (FMEA) BOT - Keyboards & Buttons
=============================================================
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# ── USER KEYBOARDS ────────────────────────────────────────────

def main_menu_keyboard(channel_link, support_link):
    """Main menu for regular users"""
    keyboard = [
        [
            InlineKeyboardButton("💰 Earning Tips", callback_data="earning_tips"),
            InlineKeyboardButton("🎯 Methods", callback_data="earn_methods"),
        ],
        [
            InlineKeyboardButton("👥 Refer & Earn", callback_data="referral"),
            InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard"),
        ],
        [
            InlineKeyboardButton("📊 My Stats", callback_data="my_stats"),
            InlineKeyboardButton("📅 Daily Updates", callback_data="daily_updates"),
        ],
        [
            InlineKeyboardButton("📢 Join Channel 🔔", url=channel_link),
            InlineKeyboardButton("💬 Support", url=support_link),
        ],
        [
            InlineKeyboardButton("ℹ️ About FMEA", callback_data="about_fmea"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_keyboard():
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)

def earning_methods_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("💻 Freelancing", callback_data="earn_freelancing"),
            InlineKeyboardButton("📈 Trading Tips", callback_data="earn_trading"),
        ],
        [
            InlineKeyboardButton("🤝 Affiliate", callback_data="earn_affiliate"),
            InlineKeyboardButton("📱 Apps से कमाई", callback_data="earn_apps"),
        ],
        [
            InlineKeyboardButton("🎬 YouTube", callback_data="earn_youtube"),
            InlineKeyboardButton("🛒 Reselling", callback_data="earn_reselling"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def share_keyboard(bot_username, ref_code):
    share_text = f"Join Free Money Earning Adda! Daily earning tips & methods 💰\n👉 {bot_username}?start={ref_code}"
    keyboard = [
        [InlineKeyboardButton("📤 Share with Friends", switch_inline_query=share_text)],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ── ADMIN KEYBOARDS ───────────────────────────────────────────

def admin_main_keyboard():
    """Main admin control panel"""
    keyboard = [
        [
            InlineKeyboardButton("📤 Broadcast Message", callback_data="admin_broadcast"),
            InlineKeyboardButton("📅 Schedule Post", callback_data="admin_schedule"),
        ],
        [
            InlineKeyboardButton("📢 Post to Channel", callback_data="admin_channel_post"),
            InlineKeyboardButton("📚 Content Library", callback_data="admin_content"),
        ],
        [
            InlineKeyboardButton("👥 User Management", callback_data="admin_users"),
            InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton("⚙️ Bot Settings", callback_data="admin_settings"),
            InlineKeyboardButton("📋 Scheduled Posts", callback_data="admin_view_posts"),
        ],
        [
            InlineKeyboardButton("🔥 Auto Promotion", callback_data="admin_promo"),
            InlineKeyboardButton("💡 Quick Post", callback_data="admin_quick_post"),
        ],
        [
            InlineKeyboardButton("🔙 Exit Admin", callback_data="main_menu"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_settings_keyboard(auto_post, welcome_msg, referral, bot_status):
    """Settings toggle keyboard"""
    auto_icon = "✅" if auto_post == 'true' else "❌"
    welcome_icon = "✅" if welcome_msg == 'true' else "❌"
    ref_icon = "✅" if referral == 'true' else "❌"
    status_icon = "🟢" if bot_status == 'active' else "🔴"
    
    keyboard = [
        [InlineKeyboardButton(f"{auto_icon} Auto Post: {'ON' if auto_post == 'true' else 'OFF'}", 
                               callback_data="toggle_auto_post")],
        [InlineKeyboardButton(f"{welcome_icon} Welcome Msg: {'ON' if welcome_msg == 'true' else 'OFF'}", 
                               callback_data="toggle_welcome")],
        [InlineKeyboardButton(f"{ref_icon} Referral: {'ON' if referral == 'true' else 'OFF'}", 
                               callback_data="toggle_referral")],
        [InlineKeyboardButton(f"{status_icon} Bot Status: {bot_status.upper()}", 
                               callback_data="toggle_bot_status")],
        [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_users_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📊 Total Users", callback_data="users_total"),
            InlineKeyboardButton("🔍 Find User", callback_data="users_find"),
        ],
        [
            InlineKeyboardButton("🚫 Block User", callback_data="users_block"),
            InlineKeyboardButton("✅ Unblock User", callback_data="users_unblock"),
        ],
        [
            InlineKeyboardButton("🏆 Top Referrers", callback_data="users_top"),
            InlineKeyboardButton("📤 Export List", callback_data="users_export"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def schedule_time_keyboard():
    """Quick time selection for scheduling"""
    keyboard = [
        [
            InlineKeyboardButton("🌅 Morning 9 AM", callback_data="sched_09:00"),
            InlineKeyboardButton("☀️ Noon 12 PM", callback_data="sched_12:00"),
        ],
        [
            InlineKeyboardButton("🌤 Afternoon 3 PM", callback_data="sched_15:00"),
            InlineKeyboardButton("🌆 Evening 6 PM", callback_data="sched_18:00"),
        ],
        [
            InlineKeyboardButton("🌙 Night 9 PM", callback_data="sched_21:00"),
            InlineKeyboardButton("🕐 Custom Time", callback_data="sched_custom"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def promo_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔥 Send Promo 1", callback_data="send_promo_1")],
        [InlineKeyboardButton("⚡ Send Promo 2", callback_data="send_promo_2")],
        [InlineKeyboardButton("💎 Send Promo 3", callback_data="send_promo_3")],
        [InlineKeyboardButton("📢 Send All Promos", callback_data="send_all_promos")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def confirm_keyboard(action):
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, Confirm", callback_data=f"confirm_{action}"),
            InlineKeyboardButton("❌ Cancel", callback_data="admin_panel"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def cancel_keyboard():
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="admin_panel")]]
    return InlineKeyboardMarkup(keyboard)
