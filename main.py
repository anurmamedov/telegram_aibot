import logging
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import openai
import requests
from io import BytesIO
import asyncio
import os
from dotenv import load_dotenv


# Loading environment variables from .env file
load_dotenv()

# Setting up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Replacing 'YOUR_OPENAI_API_KEY' with your actual OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')


async def start(update: Update, context: CallbackContext) -> None:
    logger.debug("Start command received")
    await update.message.reply_text('Hi! I am a anarcodes_ai. Ask me anything or use /generate to create an image!')

async def help_command(update: Update, context: CallbackContext) -> None:
    logger.debug("Help command received")
    await update.message.reply_text('You can ask me anything, and I will try my best to answer! Use /generate <description> to create an image.')

async def handle_message(update: Update, context: CallbackContext) -> None:
    logger.debug("Message received: %s", update.message.text)
    user_message = update.message.text
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}],
            max_tokens=150
        )
        reply = response.choices[0].message['content'].strip()
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error("Error in handle_message: %s", str(e))
        await update.message.reply_text("Sorry, there was an error processing your request.")

async def generate_image(update: Update, context: CallbackContext) -> None:
    logger.debug("Generate command received with args: %s", context.args)
    user_message = ' '.join(context.args)
    if not user_message:
        await update.message.reply_text('Please provide a description for the image.')
        return
    
    try:
        # Adding a delay of 2 seconds (adjust the time as needed)
        await asyncio.sleep(2)
        # Sending a waiting message
        waiting_message = await update.message.reply_text('Please wait, generating picture...')

        response = openai.Image.create(
            prompt=user_message,
            n=1,
            size="512x512"
        )
        logger.debug("Image response: %s", response)
        # Print the full response for debugging
        logger.debug("Full OpenAI Response: %s", response)

    
        if 'data' in response and len(response['data']) > 0 and 'url' in response['data'][0]:
            image_url = response['data'][0]['url']
            logger.debug("Image URL: %s", image_url)
            
            image_response = requests.get(image_url)
            
            image_response.raise_for_status()
            
            image = BytesIO(image_response.content)
            await update.message.reply_photo(photo=InputFile(image), caption='Here is your generated image!')
        else:
            logger.error("Invalid image response: %s", response)
            await update.message.reply_text("Sorry, there was an error generating the image.")

    except Exception as e:
        logger.error("Error in generate_image: %s", str(e))
        await update.message.reply_text(f"Sorry, there was an error generating the image: {str(e)}")

def main() -> None:
    # Replace Telegram bot token
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler("generate", generate_image))

    application.run_polling()

if __name__ == '__main__':
    main()

