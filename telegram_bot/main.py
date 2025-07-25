import logging
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters, ConversationHandler
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

ASK_START = 0
ASK_VAULT = 1

EXAMPLE_VAULTS = [
    "VAULT_ABC123",
    "VAULT_DEF456",
    "VAULT_XYZ789"
]

USER_VAULT_MAP = {}
USER_DECISION_STATS = {}

class MockRiskStrategyManager:
    def __init__(self):
        self.risk_threshold = 0.75

    def check_risk_for_account(self, account_id: str) -> float:
        import random
        return round(random.uniform(0.5, 0.95), 2)

    def get_current_threshold(self) -> float:
        return self.risk_threshold

mock_risk_manager = MockRiskStrategyManager()

async def initial_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Only show the Start button, do not allow text input
    keyboard = [[KeyboardButton("Start")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Welcome! Press 'Start' to begin.",
        reply_markup=reply_markup
    )
    return ASK_START

async def handle_start_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Only accept "Start" as input
    if update.message.text.strip().lower() == "start":
        await update.message.reply_text(
            "Please enter your vault/account address to link with rescue alerts.\n"
            f"Example addresses: {', '.join(EXAMPLE_VAULTS)}",
            reply_markup=None  # Remove custom keyboard
        )
        return ASK_VAULT
    else:
        # Ignore any other input, re-show Start button
        keyboard = [[KeyboardButton("Start")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            "Please press 'Start' to begin.",
            reply_markup=reply_markup
        )
        return ASK_START

async def ask_vault(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_chat_id = update.effective_chat.id
    vault_address = update.message.text.strip()
    USER_VAULT_MAP[user_chat_id] = vault_address
    USER_DECISION_STATS.setdefault(user_chat_id, {'accept': 0, 'refuse': 0})
    # Show options menu
    keyboard = [
        [InlineKeyboardButton("Check Risk", callback_data="menu_check_risk")],
        [InlineKeyboardButton("Show Stats", callback_data="menu_show_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Vault/account `{vault_address}` linked to your chat. You will receive rescue alerts for this address.\n"
        "Use /check_risk to get a manual risk assessment.\nChoose an option:",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_chat_id = query.from_user.id
    if query.data == "menu_check_risk":
        vault_address = USER_VAULT_MAP.get(user_chat_id)
        if not vault_address:
            await query.edit_message_text("No vault/account linked. Please enter your vault/account address.")
            return
        risk_score = mock_risk_manager.check_risk_for_account(vault_address)
        threshold = mock_risk_manager.get_current_threshold()
        status = "HIGH RISK! Rescue recommended." if risk_score >= threshold else "Low risk."
        keyboard = [
            [InlineKeyboardButton("Approve Rescue", callback_data=f"rescue_approve")],
            [InlineKeyboardButton("Deny Rescue", callback_data=f"rescue_deny")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Current risk for vault/account `{vault_address}`: {risk_score:.2f} (Threshold: {threshold:.2f}).\n"
            f"Status: {status}",
            reply_markup=reply_markup
        )
    elif query.data == "menu_show_stats":
        stats = USER_DECISION_STATS.get(user_chat_id, {'accept': 0, 'refuse': 0})
        await query.edit_message_text(
            f"Rescue stats:\nAccepted: {stats['accept']}\nRefused: {stats['refuse']}"
        )
    else:
        await query.edit_message_text("Unknown option.")

async def check_risk_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_chat_id = update.effective_chat.id
    vault_address = USER_VAULT_MAP.get(user_chat_id)
    if not vault_address:
        await update.message.reply_text("No vault/account linked. Please enter your vault/account address.")
        return

    risk_score = mock_risk_manager.check_risk_for_account(vault_address)
    threshold = mock_risk_manager.get_current_threshold()
    status = "HIGH RISK! Rescue recommended." if risk_score >= threshold else "Low risk."
    keyboard = [
        [InlineKeyboardButton("Approve Rescue", callback_data=f"rescue_approve")],
        [InlineKeyboardButton("Deny Rescue", callback_data=f"rescue_deny")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Current risk for vault/account `{vault_address}`: {risk_score:.2f} (Threshold: {threshold:.2f}).\n"
        f"Status: {status}",
        reply_markup=reply_markup
    )

async def send_rescue_alert_periodically(application):
    while True:
        for chat_id, vault_address in USER_VAULT_MAP.items():
            risk_score = mock_risk_manager.check_risk_for_account(vault_address)
            threshold = mock_risk_manager.get_current_threshold()
            if risk_score >= threshold:
                keyboard = [
                    [InlineKeyboardButton("Approve Rescue", callback_data=f"rescue_approve")],
                    [InlineKeyboardButton("Deny Rescue", callback_data=f"rescue_deny")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                message_text = (
                    f"🚨 **URGENT RESCUE ALERT** 🚨\n\n"
                    f"Vault/account `{vault_address}` detected with high risk.\n"
                    f"Risk Score: `{risk_score:.2f}` (Threshold: `{threshold:.2f}`)\n"
                    "Please decide on the next action:"
                )
                await application.bot.send_message(
                    chat_id=chat_id, text=message_text, reply_markup=reply_markup, parse_mode='Markdown'
                )
        await asyncio.sleep(10)

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_chat_id = query.from_user.id
    vault_address = USER_VAULT_MAP.get(user_chat_id, "Unknown")
    decision_stats = USER_DECISION_STATS.setdefault(user_chat_id, {'accept': 0, 'refuse': 0})

    if query.data == "rescue_approve":
        decision_stats['accept'] += 1
        response_text = (
            f"✅ Rescue for vault/account `{vault_address}` approved.\n"
            f"Total approvals: {decision_stats['accept']}, refusals: {decision_stats['refuse']}"
        )
    elif query.data == "rescue_deny":
        decision_stats['refuse'] += 1
        response_text = (
            f"❌ Rescue for vault/account `{vault_address}` denied.\n"
            f"Total approvals: {decision_stats['accept']}, refusals: {decision_stats['refuse']}"
        )
    else:
        response_text = "Invalid action."
    await query.edit_message_text(response_text)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    if update.effective_message:
        await update.effective_message.reply_text(
            "An error occurred. Please try again later or contact support."
        )

def main_telegram_bot_runner():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set. Please set it before running the bot.")

    application = ApplicationBuilder().token(token).build()

    # Conversation handler for initial menu and vault input
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.ALL, initial_menu)],
        states={
            ASK_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_start_button)],
            ASK_VAULT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_vault)],
        },
        fallbacks=[],
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("check_risk", check_risk_command))
    application.add_handler(CallbackQueryHandler(button_callback_handler, pattern=r"^rescue_(approve|deny)$"))
    application.add_handler(CallbackQueryHandler(menu_callback_handler, pattern=r"^menu_.*$"))
    application.add_error_handler(error_handler)

    loop = asyncio.get_event_loop()
    loop.create_task(send_rescue_alert_periodically(application))

    print("Telegram bot started polling...")
    application.run_polling()

if __name__ == "__main__":
    main_telegram_bot_runner()