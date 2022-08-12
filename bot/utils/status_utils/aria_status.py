from asyncio import sleep
from aria2p.client import ClientException
from time import time
from bot import EDIT_SLEEP_SECS, aria2, status_dict, LOGGER
from bot.utils.bot_utils.human_format import get_readable_file_size
from bot.utils.status_utils.misc_utils import MirrorStatus, get_bottom_status
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions import FloodWait, MessageNotModified

def get_download(gid):
    try:
        return aria2.get_download(gid)
    except Exception as e:
        LOGGER.error(f'{e}: while getting torrent info')

class AriaDownloadStatus:
    def __init__(self, gid, message):
        self.__gid = gid
        self.__download = get_download(gid)
        self.__message= message
        self.id= self.__message.id

    def __update(self):
        self.__download = self.__download.live
        if self.__download.followed_by_ids:
            self.__gid = self.__download.followed_by_ids[0]
            self.__download = get_download(self.__gid)

    async def create_status(self):
          sleeps= False
          start = time()
          while True:
               try:
                    if not self.__download.is_complete:
                         if not self.__download.error_message:
                              sleeps = True
                              update_message= self.create_status_message()
                              if time() - start > EDIT_SLEEP_SECS:
                                   start = time()     
                                   try:
                                        data = "cancel_aria2_{}".format(self.__gid)
                                        await self.__message.edit(update_message, reply_markup=(InlineKeyboardMarkup([
                                                  [InlineKeyboardButton('Cancel', callback_data=data.encode("UTF-8"))]
                                                  ])))
                                   except FloodWait as fw:
                                          await sleep(fw.value)
                                   except MessageNotModified:
                                          await sleep(1)

                              if sleeps:
                                   if self.__download.is_complete:
                                        del status_dict[self.id]
                                        return True   
                                   sleeps = False
                                   await sleep(2)
               except ClientException as ex:
                    if " not found" in str(ex) or "'file'" in str(ex):
                         LOGGER.info("Download stopped by user!")     
                         return False
               except Exception as ex:
                    if " not found" in str(ex) or "'file'" in str(ex):
                         LOGGER.info("Download stopped by user!")   
                         return False

    def create_status_message(self):
        self.__update()
        downloading_dir_name = "N/A"
        try:
            downloading_dir_name = str(self.__download.name)
        except:
            pass
        msg = "<b>Name:</b>{}\n".format(downloading_dir_name)
        msg += "<b>Status:</b>\n".format(self.status())
        msg += "{}\n".format(self.get_progress_bar_string())
        msg += "<b>P:</b> {}%\n".format(round(self.__download.progress, 2))
        msg += "<b>Downloaded:</b> {} <b>of:</b> {}\n".format(get_readable_file_size(self.__download.completed_length), self.__download.total_length_string())
        msg += "<b>Speed:</b> {}".format(self.__download.download_speed_string()) + "|" + "<b>ETA: {} Mins\n</b>".format(self.__download.eta_string())
        try:
            msg += f"<b>Seeders:</b> {self.__download.num_seeders}" 
            msg += f" | <b>Peers:</b> {self.__download.connections}"
        except:
            pass
        try:
            msg += f"<b>Seeders:</b> {self.__download.num_seeds}"
            msg += f" | <b>Leechers:</b> {self.__download.num_leechs}"
        except:
            pass
        msg += get_bottom_status()
        return msg

    def get_progress_bar_string(self):
        completed = self.__download.completed_length / 8
        total = self.__download.total_length / 8
        p = 0 if total == 0 else round(completed * 100 / total)
        p = min(max(p, 0), 100)
        cFull = p // 8
        p_str = '■' * cFull
        p_str += '□' * (12 - cFull)
        p_str = f"[{p_str}]"
        return p_str
        
    def status(self):
        download = self.__download
        if download.is_waiting:
            return MirrorStatus.STATUS_WAITING
        elif download.is_paused:
            return MirrorStatus.STATUS_PAUSED
        else:
            return MirrorStatus.STATUS_DOWNLOADING

    def download(self):
        return self

    def gid(self):
        self.__update()
        return self.__gid

    def cancel_download(self):
        self.__update()
        if len(self.__download.followed_by_ids) != 0:
            LOGGER.info(f"Cancelling Download.")
            downloads = aria2.get_downloads(self.__download.followed_by_ids)
            aria2.remove(downloads, force=True, files=True)
        else:
            LOGGER.info(f"Cancelling Download.")
        del status_dict[self.id]
        aria2.remove([self.__download], force=True, files=True)