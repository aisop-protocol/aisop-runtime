import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from src.config import TELEGRAM_BOT_TOKEN, logger
from src.llm_client import AIClient

# Initialize AI Client
ai_client = AIClient()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I am an AISOP-powered AI Bot. Send me a message!",
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send user message to AI and stream response."""
    user_message = update.message.text
    logger.info(f"Received message from {update.effective_user.name}: {user_message}")

    # Send initial placeholder message
    placeholder_message = await update.message.reply_text("Thinking...")
    
    full_response = ""
    last_update_time = time.time()
    update_interval = 0.6  # Optimal balance for Snappy UI and Rate Limiting

    try:
        async for chunk in ai_client.get_streaming_response(user_message):
            full_response += chunk
            
            # Periodically update the message
            if time.time() - last_update_time > update_interval:
                if full_response.strip():
                    try:
                        # Update the latest portion of the message
                        display_text = full_response
                        if len(display_text) > 4000:
                            display_text = "...(continued)...\n" + display_text[-3800:]
                        
                        await context.bot.edit_message_text(
                            chat_id=placeholder_message.chat_id,
                            message_id=placeholder_message.message_id,
                            text=display_text + "..."
                        )
                    except Exception:
                        pass # Ignore frequent update errors
                last_update_time = time.time()

        # Final update - handle very long messages by sending multiple if needed
        final_text = full_response if full_response.strip() else "Empty response from AI."
        
        # Split into 4000 char chunks
        MAX_LEN = 4000
        chunks = [final_text[i:i+MAX_LEN] for i in range(0, len(final_text), MAX_LEN)]
        
        # Update first message
        await context.bot.edit_message_text(
            chat_id=placeholder_message.chat_id,
            message_id=placeholder_message.message_id,
            text=chunks[0]
        )
        
        # Send remaining as new messages
        for extra_chunk in chunks[1:]:
            await update.message.reply_text(extra_chunk)

    except Exception as e:
        logger.error(f"Error in streaming handler: {e}")
        try:
            await context.bot.edit_message_text(
                chat_id=placeholder_message.chat_id,
                message_id=placeholder_message.message_id,
                text=f"Error: {e}"
            )
        except:
             await update.message.reply_text(f"Critical Error: {e}")

def run_bot():
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("No Telegram Token provided. Exiting.")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    logger.info("Bot execution started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
