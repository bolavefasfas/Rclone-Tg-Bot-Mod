
from bot import EDIT_SLEEP_SECS, LOGGER, status_dict
from time import time
from asyncio import sleep
from bot.utils.bot_utils.bot_utils import get_readable_time
from bot.utils.bot_utils.human_format import get_readable_file_size
from bot.utils.bot_utils.message_utils import editMessage, sendMessage
from bot.utils.status_utils.misc_utils import MirrorStatus, get_bottom_status
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions import FloodWait, MessageNotModified

class qBitTorrentStatus:
    def __init__(self, message, obj):
        self.__message= message
        self.id= self.__message.id
        self.__obj = obj
        self.__is_cancelled= False

    async def create_status(self):
        message = await sendMessage("Starting Download", self.__message)
        start = time()
        sleeps= False
        while True:
            sleeps = True
            try:
                tor_info = self.__obj.client.torrents_info(torrent_hashes=self.__obj.ext_hash)[0]
            except Exception as e:
                LOGGER.error(f'{e}: while getting torrent info')
            status_message= self.create_status_message(tor_info)
            if time() - start > EDIT_SLEEP_SECS:
                start = time()       
                try:
                    data = "cancel_qbitdl_{}".format(self.__obj.ext_hash[:12])
                    await editMessage(status_message, message, reply_markup=(InlineKeyboardMarkup([
                                            [InlineKeyboardButton('Cancel', callback_data=data.encode("UTF-8"))]
                                            ])))
                except FloodWait as fw:
                    await sleep(fw.value)
                except MessageNotModified:
                    await sleep(1)

                if sleeps:
                    if self.__is_cancelled:     
                        del status_dict[self.id]   
                        await editMessage("Download cancelled!", message)
                        return False
                    if self.__obj.uploaded:
                        del status_dict[self.id]   
                        self.__obj.periodic.cancel()    
                        return True     
                    sleeps = False
                    await sleep(1)

    def create_status_message(self, tor_info):
        if self.__obj.select:
            size= tor_info.size
        else:
            size= tor_info.total_size

        download = tor_info.state
        if download in ["queuedDL", "queuedUP"]:
            status= MirrorStatus.STATUS_WAITING
        elif download in ["pausedDL", "pausedUP"]:
            status= MirrorStatus.STATUS_PAUSED
        elif download in ["checkingUP", "checkingDL"]:
            status= MirrorStatus.STATUS_CHECKING
        else:
            status= MirrorStatus.STATUS_DOWNLOADING

        msg = "<b>Name:</b>{}\n".format(tor_info.name)
        msg += f"<b>Status:</b> {status}\n"
        msg += "{}\n".format(self.get_progress_bar_string(tor_info))
        msg += "<b>P:</b>{}\n".format(f'{round(tor_info.progress*100, 2)}%')
        msg += "<b>Downloaded:</b> {} <b>of:</b> {}\n".format(get_readable_file_size(tor_info.downloaded), get_readable_file_size(size))
        msg += "<b>Speed:</b> {}".format(f"{get_readable_file_size(tor_info.dlspeed)}/s") + "|" + "<b>ETA: {}\n</b>".format(get_readable_time(tor_info.eta))
        try:
            msg += f"<b>Seeders:</b> {tor_info.num_seeds}" \
                    f" | <b>Leechers:</b> {tor_info.num_leechs}\n"
        except:
            pass
        msg += get_bottom_status()
        return msg 

    def get_progress_bar_string(self, tor_info):
        completed = tor_info.downloaded / 8
        total = tor_info.total_size / 8
        p = 0 if total == 0 else round(completed * 100 / total)
        p = min(max(p, 0), 100)
        cFull = p // 8
        p_str = '■' * cFull
        p_str += '□' * (12 - cFull)
        p_str = f"[{p_str}]"
        return p_str

    def client(self):
        return self.__obj.client

    def gid(self):
        return self.__obj.ext_hash[:12]

    def message(self):
        return self.__message

    def name(self):
        return self.__obj.name
        
    def cancel_download(self):
        self.__is_cancelled= True
        self.__obj.onDownloadError('Download stopped by user!')