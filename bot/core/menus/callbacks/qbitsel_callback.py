
from os import remove, path as ospath
from bot import LOGGER
from ....uploaders.rclone.rclone_mirror import RcloneMirror
from bot.utils.bot_utils.misc_utils import getDownloadByGid


async def get_confirm(update, callback_query):
    query = callback_query
    data = query.data.split()
    message= query.message
    tag= f"@{message.reply_to_message.from_user.username}"
    id = data[3]
    dl = getDownloadByGid(data[2])
    name= dl.name()
    if data[1] == "pin":
        await query.answer(text=data[3], show_alert=True)
    elif data[1] == "done":
        await query.answer()
        if len(id) > 20:
            client = dl.client()
            tor_info = client.torrents_info(torrent_hash=id)[0]
            path = tor_info.content_path.rsplit('/', 1)[0]
            res = client.torrents_files(torrent_hash=id)
            for f in res:
                LOGGER.info('before f.priority')     
                if f.priority == 0:
                    LOGGER.info('after f.priority')       
                    f_paths = [f"{path}/{f.name}", f"{path}/{f.name}.!qB"]
                    for f_path in f_paths:
                       if ospath.exists(f_path):
                           try:
                               remove(f_path)
                           except:
                               pass
            client.torrents_resume(torrent_hashes=id)
            status= await dl.create_status()
            if status:
                rclone_mirror= RcloneMirror(path, message, tag, tor_name=name)   
                await rclone_mirror.mirror() 
            else:
                await query.message.delete()    