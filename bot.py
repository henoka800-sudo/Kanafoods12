# KANA FOODS ORDER BOT
# This script requires the 'python-telegram-bot' library: pip install python-telegram-bot

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Configuration ---
# WARNING: This is the user-provided token. Keep your tokens secure in real-world applications.
TOKEN = '8422253254:AAFrac-FRl65zjZQ-T7d0B4uZ0yv90HiX2s'
GENERAL_CONTACT = '0086465604'
CUSTOMER_SERVICE_BOT = '@kana_foods_bot' # Placeholder, as the actual bot name is 'kana foods'

# Product Inventory (Price per unit/kg)
PRODUCTS = {
    "mozzarella_cheese": {"name": "🧀 Mozzarella Cheese", "price": 800, "unit": "per unit"},
    "provolone_cheese": {"name": "🧀 Provolone Cheese", "price": 930, "unit": "per unit"},
    "chicken_whole": {"name": "🐔 Whole Chicken", "price": 650, "unit": "per unit"},
    "chicken_breast": {"name": "🍗 Chicken Breast", "price": 1080, "unit": "per kg"},
    "table_butter": {"name": "🧈 Table Butter", "price": 240, "unit": "per unit"},
}

# In-memory storage for user carts: {user_id: {product_key: quantity}}
user_carts = {}

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Utility Functions ---

def get_product_list_keyboard():
    """Generates the inline keyboard for the product menu."""
    keyboard = []
    for key, product in PRODUCTS.items():
        button_text = f"{product['name']} - {product['price']} ({product['unit']})"
        # Callback data format: 'add_{product_key}'
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"add_{key}")]
        )
    # Add a button to view the cart
    keyboard.append([InlineKeyboardButton("🛒 View Cart and Checkout", callback_data='view_cart')])
    return InlineKeyboardMarkup(keyboard)

def get_cart_summary(user_id):
    """Calculates the total and formats the cart content for display."""
    cart = user_carts.get(user_id, {})
    if not cart:
        return "Your cart is currently empty! Use /menu to start ordering.", 0

    summary = ["*🛒 Your Current Order (Kana Foods)*\n"]
    total_cost = 0

    for key, quantity in cart.items():
        if quantity > 0 and key in PRODUCTS:
            product = PRODUCTS[key]
            line_total = product['price'] * quantity
            total_cost += line_total
            summary.append(
                f"• {quantity}x {product['name']} @ {product['price']} = {line_total}"
            )

    summary.append(f"\n*💰 Total Cost: {total_cost}*")
    return "\n".join(summary), total_cost

# --- Command Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message and main options."""
    user = update.effective_user
    welcome_text = (
        f"Hello, {user.full_name}! Welcome to the **Kana Foods** order bot.\n\n"
        "I can help you place bulk orders for high-quality food products.\n\n"
        "Use /menu to see our products or /cart to view your current order."
    )
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown'
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the product menu with 'Add to Cart' buttons."""
    reply_markup = get_product_list_keyboard()
    await update.message.reply_text(
        "*🍽️ Kana Foods Product Catalog*\n\n"
        "Tap a product to add one unit to your cart. View your cart to adjust quantities.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def cart_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the current cart contents and total."""
    user_id = update.effective_user.id
    summary, _ = get_cart_summary(user_id)

    # Keyboard for cart actions
    keyboard = [
        [InlineKeyboardButton("✅ Checkout Order", callback_data='checkout')],
        [InlineKeyboardButton("🗑️ Clear Cart", callback_data='clear_cart')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        summary,
        reply_markup=reply_markup if user_carts.get(user_id) else None,
        parse_mode='Markdown'
    )

async def checkout_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Finalizes the order and provides contact details."""
    user_id = update.effective_user.id
    summary, total_cost = get_cart_summary(user_id)

    if not user_carts.get(user_id):
        await update.message.reply_text("Your cart is empty. Nothing to check out.")
        return

    # 1. Prepare Order Details
    order_details = summary + "\n\n"
    order_details += (
        "*--- Next Steps ---*\n"
        "To finalize your order, please copy your order details above and contact us using the information below. "
        "Mention your order total and User ID.\n\n"
        f"**📞 General Contact:** `{GENERAL_CONTACT}`\n"
        f"**👤 Your User ID:** `{user_id}`\n\n"
        "*Your cart has been cleared.* Thank you for ordering with Kana Foods!"
    )

    # 2. Send Checkout Message
    await update.message.reply_text(
        order_details,
        parse_mode='Markdown'
    )

    # 3. Clear Cart after successful "checkout"
    if user_id in user_carts:
        del user_carts[user_id]


# --- Callback Query Handler (Inline Button Clicks) ---

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles all inline button presses (Add, View Cart, Clear, Checkout)."""
    query = update.callback_query
    await query.answer() # Acknowledge the button press

    user_id = query.from_user.id
    data = query.data

    if data.startswith('add_'):
        # Action: Add item to cart
        product_key = data[4:] # Extract product key after 'add_'

        # Initialize cart if it doesn't exist
        if user_id not in user_carts:
            user_carts[user_id] = {}

        # Increment quantity
        current_quantity = user_carts[user_id].get(product_key, 0)
        user_carts[user_id][product_key] = current_quantity + 1

        product_name = PRODUCTS.get(product_key, {}).get("name", "Item")
        await query.edit_message_caption(
            caption=f"Added 1x {product_name}. Total in cart: {current_quantity + 1}.",
            reply_markup=get_product_list_keyboard()
        )

    elif data == 'view_cart':
        # Action: View Cart
        summary, _ = get_cart_summary(user_id)
        keyboard = [
            [InlineKeyboardButton("✅ Checkout Order", callback_data='checkout')],
            [InlineKeyboardButton("🗑️ Clear Cart", callback_data='clear_cart')],
            [InlineKeyboardButton("⬅️ Back to Menu", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            summary,
            reply_markup=reply_markup if user_carts.get(user_id) else get_product_list_keyboard(),
            parse_mode='Markdown'
        )

    elif data == 'clear_cart':
        # Action: Clear Cart
        if user_id in user_carts:
            del user_carts[user_id]
            message = "🗑️ Your cart has been completely cleared."
        else:
            message = "Your cart was already empty."

        await query.edit_message_text(
            message + "\n\nUse /menu to start a new order.",
            reply_markup=get_product_list_keyboard()
        )

    elif data == 'checkout':
        await checkout_command(query, context)

    elif data == 'back_to_menu':
        reply_markup = get_product_list_keyboard()
        await query.edit_message_text(
            "*🍽️ Kana Foods Product Catalog*\n\n"
            "Tap a product to add one unit to your cart. View your cart to adjust quantities.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


# --- Main Function ---

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("cart", cart_command))
    application.add_handler(CommandHandler("checkout", checkout_command))
    application.add_handler(CallbackQueryHandler(button_callback))

    print("Bot is running... Press Ctrl-C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
