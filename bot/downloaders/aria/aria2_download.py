import asyncio
from bot import DOWNLOAD_DIR, LOGGER
from os import path as ospath
from bot import aria2, status_dict
from bot.utils.bot_utils.bot_utils import is_magnet
from bot.utils.bot_utils.message_utils import sendMessage
from bot.utils.status_utils.aria_status import AriaDownloadStatus

class Aria2Downloader():
    def __init__(self, link, message):
        super().__init__()
        self._loop = asyncio.get_event_loop()
        self.link = link
        self._gid = 0
        self.__message= message
        self.id= self.__message.id
        self._download= None

    async def execute(self):
        path= f'{DOWNLOAD_DIR}{self.id}'
        
        if is_magnet(self.link):
            download = await self._loop.run_in_executor(None, aria2.add_magnet, self.link, {'dir': path})
        else:
            download = await self._loop.run_in_executor(None, aria2.add_uris, [self.link], {'dir': path} )
       
        if download.error_message:
            error = str(download.error_message).replace('<', ' ').replace('>', ' ')
            await sendMessage(error, self.__message)
            return False, None

        aria_status= AriaDownloadStatus(download.gid, self.__message)
        status_dict[self.id] = aria_status
        LOGGER.info("Aria2 Download started...")
        status, msg = await aria_status.create_status()
        if status:
            file_path = ospath.join(download.dir, download.name)
            await sendMessage(msg, self.__message)
            return True, file_path
        else:
            await sendMessage(msg, self.__message)     
            return False, None    