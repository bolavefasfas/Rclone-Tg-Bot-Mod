#Modified from: (c) YashDK [yash-dk@github]

import pathlib
from bot import DOWNLOAD_DIR, LOGGER, status_dict
from bot.utils.bot_utils.bot_utils import setInterval
from bot.utils.bot_utils.message_utils import sendMessage
from bot.utils.status_utils.mega_status import MegaDownloadStatus
from megasdkrestclient import MegaSdkRestClient, errors, constants
from asyncio import get_event_loop
from functools import partial


class MegaDownloader():
    POLLING_INTERVAL = 3

    def __init__(self, link, message):
        super().__init__()
        self._link = link
        self.mega_client = MegaSdkRestClient('http://localhost:6090')
        self._message = message
        self.id= self._message.id
        self.loop = get_event_loop()
        self.name= ""
        self.__periodic= None
        self.cancelled= False
        self.completed= False
        self.dl_add_info= None

    async def execute(self):
        path= f'{DOWNLOAD_DIR}{self.id}'
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        LOGGER.info("Mega Download Started...")
        
        try:
            self.dl_add_info = await self.loop.run_in_executor(None, partial(self.mega_client.addDl, self._link, path))
        except errors.MegaSdkRestClientException as e:
            error_reason = str(dict(e.message)["message"]).title()
            await sendMessage(error_reason, self._message)
            return False, None

        self.gid = self.dl_add_info["gid"]
        self.__periodic = setInterval(self.POLLING_INTERVAL, self.__onInterval)
        mega_status= MegaDownloadStatus(self.gid, self._message, self)
        status_dict[self.id] = mega_status
        status, path= await mega_status.create_status()
        if status:
            return True, path  
        else:
            return False, None       

    def __onInterval(self):
        dlInfo = self.mega_client.getDownloadInfo(self.gid)
        self.name = dlInfo['name']
        if dlInfo['state'] in [constants.State.TYPE_STATE_COMPLETED, constants.State.TYPE_STATE_CANCELED, 
            constants.State.TYPE_STATE_FAILED] and self.__periodic is not None:
            self.__periodic.cancel()
        if dlInfo['state'] == constants.State.TYPE_STATE_COMPLETED:
            self.completed= True
            return
        if dlInfo['state'] == constants.State.TYPE_STATE_CANCELED:
            self.__onDownloadError('Download stopped by user!')
            return
        if dlInfo['state'] == constants.State.TYPE_STATE_FAILED:
            self.__onDownloadError(dlInfo['error_string'])
            return
    
    def __onDownloadError(self, message):
        LOGGER.info(f"Cancelling Download: {self.name}, cause: {message}")     
        self.cancelled= True
        self.__periodic.cancel()
        
    

