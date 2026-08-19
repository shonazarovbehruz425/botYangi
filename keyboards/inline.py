import urllib.parse
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import WEBAPP_URL

def get_register_keyboard(referrer_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ RO'YXATDAN O'TISH",
                    callback_data=f"confirm_reg:{referrer_id}"
                )
            ]
        ]
    )


def get_main_menu_keyboard(user_id: int = None) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="♦️ Asosiy menyu ♦️",
                callback_data="menu_header"
            )
        ],
        [
            InlineKeyboardButton(
                text="Marketing",
                callback_data="menu_marketing"
            ),
            InlineKeyboardButton(
                text="Kabinet",
                callback_data="menu_cabinet"
            )
        ]
    ]
    if WEBAPP_URL and WEBAPP_URL.startswith("https://"):
        target_url = f"{WEBAPP_URL}?user_id={user_id}" if user_id else WEBAPP_URL
        buttons.append([
            InlineKeyboardButton(text="📱 Mini App", web_app=WebAppInfo(url=target_url))
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ==================== MARKETING KEYBOARDS (4 SCREENSHOTS) ====================

def get_marketing_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1-Daraja", callback_data="mkt_lvl:1"),
                InlineKeyboardButton(text="Barcha darajalar", callback_data="mkt_all_levels")
            ],
            [
                InlineKeyboardButton(
                    text="♦️ Asosiy menyu ♦️",
                    callback_data="back_to_main_menu"
                )
            ]
        ]
    )


def get_all_levels_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1-Daraja", callback_data="mkt_lvl:1:all"),
                InlineKeyboardButton(text="2-Daraja", callback_data="mkt_lvl:2:all"),
                InlineKeyboardButton(text="3-Daraja", callback_data="mkt_lvl:3:all")
            ],
            [
                InlineKeyboardButton(text="4-Daraja", callback_data="mkt_lvl:4:all"),
                InlineKeyboardButton(text="5-Daraja", callback_data="mkt_lvl:5:all")
            ],
            [
                InlineKeyboardButton(
                    text="♦️ Asosiy menyu ♦️",
                    callback_data="back_to_main_menu"
                )
            ]
        ]
    )


def get_payment_request_keyboard(level: int, curator_id: int, curator_username: str = "", from_all: bool = False) -> InlineKeyboardMarkup:
    back_target = "mkt_all_levels" if from_all else "menu_marketing"
    # Always use tg://user?id= - guaranteed to open the exact person's chat regardless of username
    contact_url = f"tg://user?id={curator_id}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Я оплатил", callback_data=f"mkt_paid:{level}:{curator_id}"),
                InlineKeyboardButton(text="Написать", url=contact_url)
            ],
            [
                InlineKeyboardButton(text="Orqaga", callback_data=back_target)
            ]
        ]
    )


def get_payment_sent_keyboard(curator_id: int, curator_username: str = "") -> InlineKeyboardMarkup:
    # Always use tg://user?id= - guaranteed to open the exact person's chat regardless of username
    contact_url = f"tg://user?id={curator_id}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Написать", url=contact_url)
            ],
            [
                InlineKeyboardButton(text="♦️ Asosiy menyu ♦️", callback_data="back_to_main_menu")
            ]
        ]
    )


def get_curator_approval_keyboard(buyer_id: int, level: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ To'lovni tasdiqlash", callback_data=f"approve_lvl:{buyer_id}:{level}")
            ],
            [
                InlineKeyboardButton(text="💬 Foydalanuvchiga yozish", url=f"tg://user?id={buyer_id}")
            ]
        ]
    )


def get_level_locked_keyboard(level: int, cur_refs: int = 0, req_refs: int = 0, from_all: bool = False) -> InlineKeyboardMarkup:
    back_target = "mkt_all_levels" if from_all else "menu_marketing"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Orqaga", callback_data=back_target)
            ]
        ]
    )


def get_level_unlock_ready_keyboard(level: int, from_all: bool = False) -> InlineKeyboardMarkup:
    back_target = "mkt_all_levels" if from_all else "menu_marketing"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Orqaga", callback_data=back_target)
            ]
        ]
    )


def get_level_back_keyboard(from_all: bool = False) -> InlineKeyboardMarkup:
    back_target = "mkt_all_levels" if from_all else "menu_marketing"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Orqaga", callback_data=back_target)
            ]
        ]
    )


def get_level_activate_keyboard(level: int, price: int = 0, from_all: bool = False) -> InlineKeyboardMarkup:
    back_target = "mkt_all_levels" if from_all else "menu_marketing"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"💳 {level}-Darajani faollashtirish", callback_data=f"mkt_lvl:{level}")
            ],
            [
                InlineKeyboardButton(text="Orqaga", callback_data=back_target)
            ]
        ]
    )


# ==================== KABINET KEYBOARDS ====================

def get_cabinet_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="♦️ Shaxsiy Kabinet ♦️",
                    callback_data="cabinet_header"
                )
            ],
            [
                InlineKeyboardButton(text="Mening hisobim", callback_data="cab_account"),
                InlineKeyboardButton(text="Hamkorlar", callback_data="cab_partners")
            ],
            [
                InlineKeyboardButton(text="Jamoa chati", callback_data="cab_team_chat"),
                InlineKeyboardButton(text="Mening balansim", callback_data="cab_balance")
            ],
            [
                InlineKeyboardButton(
                    text="♦️ Asosiy menyu ♦️",
                    callback_data="back_to_main_menu"
                )
            ]
        ]
    )


def get_account_keyboard(chat_link: str = "https://t.me/Buyukhayot_bot") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔗 GURUHNI KO'RISH", url=chat_link)
            ],
            [
                InlineKeyboardButton(
                    text="♦️ Shaxsiy Kabinet ♦️",
                    callback_data="cabinet_header"
                )
            ],
            [
                InlineKeyboardButton(text="Mening hisobim", callback_data="cab_account"),
                InlineKeyboardButton(text="Hamkorlar", callback_data="cab_partners")
            ],
            [
                InlineKeyboardButton(text="Jamoa chati", callback_data="cab_team_chat"),
                InlineKeyboardButton(text="Mening balansim", callback_data="cab_balance")
            ],
            [
                InlineKeyboardButton(
                    text="♦️ Asosiy menyu ♦️",
                    callback_data="back_to_main_menu"
                )
            ]
        ]
    )


def get_team_chat_keyboard(chat_link: str = "https://t.me/Buyukhayot_bot") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👥 Jamoa guruhiga kirish", url=chat_link)
            ],
            [
                InlineKeyboardButton(
                    text="♦️ Shaxsiy Kabinet ♦️",
                    callback_data="cabinet_header"
                )
            ],
            [
                InlineKeyboardButton(text="Mening hisobim", callback_data="cab_account"),
                InlineKeyboardButton(text="Hamkorlar", callback_data="cab_partners")
            ],
            [
                InlineKeyboardButton(text="Jamoa chati", callback_data="cab_team_chat"),
                InlineKeyboardButton(text="Mening balansim", callback_data="cab_balance")
            ],
            [
                InlineKeyboardButton(
                    text="♦️ Asosiy menyu ♦️",
                    callback_data="back_to_main_menu"
                )
            ]
        ]
    )


def get_balance_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Mening balansim", callback_data="balance_header")
            ],
            [
                InlineKeyboardButton(text="USDT BEP20", callback_data="wallet:wallet_bep20"),
                InlineKeyboardButton(text="KARTA BANKA", callback_data="wallet:wallet_card")
            ],
            [
                InlineKeyboardButton(text="USDT TRC20", callback_data="wallet:wallet_trc20"),
                InlineKeyboardButton(text="PAYEER", callback_data="wallet:wallet_payeer")
            ],
            [
                InlineKeyboardButton(text="Tarix", callback_data="bal_history"),
                InlineKeyboardButton(text="Darajalar arxivi", callback_data="bal_archive")
            ],
            [
                InlineKeyboardButton(text="♦️ Shaxsiy Kabinet ♦️", callback_data="menu_cabinet"),
                InlineKeyboardButton(text="♦️ Asosiy menyu ♦️", callback_data="back_to_main_menu")
            ]
        ]
    )


def get_partners_keyboard(bot_username: str, user_id: int) -> InlineKeyboardMarkup:
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    share_text = f"Salom! BUYUK HAYOTGA YO'L dasturi orqali daromad olish imkoniyati. Havola orqali ro'yxatdan o'ting: {ref_link}"
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(ref_link)}&text={urllib.parse.quote(share_text)}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔗 Referal havola", callback_data="cab_ref_link")
            ],
            [
                InlineKeyboardButton(text="📤 Do'stlarga ulashish", url=share_url)
            ],
            [
                InlineKeyboardButton(text="♦️ Shaxsiy Kabinet ♦️", callback_data="menu_cabinet"),
                InlineKeyboardButton(text="♦️ Asosiy menyu ♦️", callback_data="back_to_main_menu")
            ]
        ]
    )


def get_wallet_edit_keyboard(wallet_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Hamyonni kiritish / o'zgartirish", callback_data=f"setwallet:{wallet_key}")
            ],
            [
                InlineKeyboardButton(text="🔙 Balans bo'limiga qaytish", callback_data="cab_balance"),
                InlineKeyboardButton(text="♦️ Asosiy menyu ♦️", callback_data="back_to_main_menu")
            ]
        ]
    )


def get_referrals_pagination_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"cab_team_page:{page - 1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"📄 {page}/{max(total_pages, 1)}", callback_data="noop"))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"cab_team_page:{page + 1}"))

    return InlineKeyboardMarkup(
        inline_keyboard=[
            nav_buttons,
            [
                InlineKeyboardButton(text="👥 Hamkorlar bo'limi", callback_data="cab_partners"),
                InlineKeyboardButton(text="♦️ Shaxsiy Kabinet ♦️", callback_data="menu_cabinet")
            ]
        ]
    )


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="♦️ Asosiy menyu ♦️", callback_data="back_to_main_menu")
            ]
        ]
    )


def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
                InlineKeyboardButton(text="🔗 Admin taklif havolasi", callback_data="admin_ref")
            ],
            [
                InlineKeyboardButton(text="📢 Barchaga xabar (Broadcast)", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton(text="♦️ Asosiy menyu ♦️", callback_data="back_to_main_menu")
            ]
        ]
    )
