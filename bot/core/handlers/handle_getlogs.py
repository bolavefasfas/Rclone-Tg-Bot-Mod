from bot.utils.bot_utils.admin_check import is_admin


async def get_logs(e):
    if await is_admin(e.sender_id):
        await e.client.send_file(
            entity= e.chat_id,
            file= "botlog.txt",
            reply_to= e.message.id
        )
    else:
        await e.reply('Not Authorized user')  