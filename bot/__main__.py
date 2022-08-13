from bot.core.handlermanager import add_handlers
from bot.utils.bot_utils.misc_utils import start_cleanup
from . import bot

print("Successfully deployed!")

def main():      
    start_cleanup()
    add_handlers(bot)
main()

try:
    bot.loop.run_until_complete()
except:
    pass

bot.run_until_disconnected()

