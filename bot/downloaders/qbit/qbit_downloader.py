#**************************************************
# Adapted from:
# Source: https://github.com/anasty17/mirror-leech-telegram-bot/blob/master/bot/helper/mirror_utils/download_utils/qbit_downloader.py
#**************************************************/

from hashlib import sha1
from base64 import b16encode, b32decode
from bencoding import bencode, bdecode
from re import search as re_search
from time import sleep, time
from bot import BASE_URL, DOWNLOAD_DIR, status_dict
from bot import get_client, TORRENT_TIMEOUT, LOGGER
from bot.utils.bot_utils.bot_utils import setInterval
from bot.utils.bot_utils.message_utils import deleteMessage, sendMarkup, sendMessage
from bot.utils.bot_utils.misc_utils import bt_selection_buttons
from bot.utils.status_utils.misc_utils import clean_unwanted
from bot.utils.status_utils.qbit_status import qBitTorrentStatus

class QbDownloader:
    POLLING_INTERVAL = 3

    def __init__(self, message):
        self.periodic = None
        self.path = ''
        self.name = ''
        self.ext_hash = ''
        self.__message= message
        self.id= self.__message.id
        self.select = False
        self.client = None
        self.__stalled_time = time()
        self.uploaded= False
        self.__rechecked = False

    async def add_qb_torrent(self, link, select):
        self.path= f'{DOWNLOAD_DIR}{self.id}'
        self.select = select
        self.client = get_client()
        try:
            if link.startswith('magnet:'):
                self.ext_hash = _get_hash_magnet(link)
            else:
                self.ext_hash = _get_hash_file(link)
            tor_info = self.client.torrents_info(torrent_hashes=self.ext_hash)
            if len(tor_info) > 0:
                await sendMessage("This Torrent already added!", self.__message)
                return self.client.auth_log_out()
            if link.startswith('magnet:'):
                op = self.client.torrents_add(link, save_path=self.path)
            else:
                op = self.client.torrents_add(torrent_files=[link], save_path=self.path)
            sleep(0.3)

            if op.lower() == "ok.":
                tor_info = self.client.torrents_info(torrent_hashes=self.ext_hash)
                if len(tor_info) == 0:
                    while True:
                        tor_info = self.client.torrents_info(torrent_hashes=self.ext_hash)
                        if len(tor_info) > 0:
                            break
                        elif time() - self.__stalled_time >= 12:
                            msg = "This Torrent already added or not a torrent. If something wrong please report."
                            self.client.torrents_delete(torrent_hashes=self.ext_hash, delete_files=True)
                            await sendMessage(msg, self.__message)
                            self.client.auth_log_out()
                            return False, None, None
            else:
                msg = "This is an unsupported/invalid link." 
                await sendMessage(msg, self.__message)   
                self.client.auth_log_out()
                return False, None, None
            
            tor_info = tor_info[0]
            self.name = tor_info.name
            self.ext_hash = tor_info.hash
            self.periodic = setInterval(self.POLLING_INTERVAL, self.__qb_listener)
            self._qb_status= qBitTorrentStatus(self.__message, self)
            status_dict[self.id] = self._qb_status
            LOGGER.info(f"QbitDownload started: {self.name} - Hash: {self.ext_hash}")
            if BASE_URL is not None and select:
                if link.startswith('magnet:'):
                    metamsg = "Downloading Metadata, wait then you can select files. Use torrent file to avoid this wait."
                    meta= await sendMessage(metamsg, self.__message)
                    while True:
                        tor_info = self.client.torrents_info(torrent_hashes=self.ext_hash)
                        if len(tor_info) == 0:
                            await deleteMessage(meta)
                            return False, None, None
                        try:
                            tor_info = tor_info[0]
                            if tor_info.state not in ["metaDL", "checkingResumeData", "pausedDL"]:
                                await deleteMessage(meta)    
                                break
                        except:
                            await deleteMessage(meta)     
                            return False, None, None
                self.client.torrents_pause(torrent_hashes= self.ext_hash)
                SBUTTONS = bt_selection_buttons(self.ext_hash)
                msg = "Your download paused. Choose files then press Done Selecting button to start downloading."
                await sendMarkup(msg, self.__message, reply_markup=SBUTTONS)
                return False, None, None
            else:
                status= await self._qb_status.create_status()
                if status:
                    return True, self.path, self.name
                else:
                    return False, None, None
        except Exception as e:
            LOGGER.info(str(e))
            self.client.auth_log_out()
            return False, None, None

    def __qb_listener(self):
        try:
            tor_info = self.client.torrents_info(torrent_hashes=self.ext_hash)
            if len(tor_info) == 0:
                return
            tor_info = tor_info[0]
            if tor_info.state == "metaDL":
                self.__stalled_time = time()
                if TORRENT_TIMEOUT is not None and time() - tor_info.added_on >= TORRENT_TIMEOUT:
                    self.onDownloadError("Dead Torrent!")
            elif tor_info.state == "downloading":
                self.__stalled_time = time()
            elif tor_info.state == "stalledDL":
                if not self.__rechecked and 0.99989999999999999 < tor_info.progress < 1:
                    msg = f"Force recheck - Name: {self.name} Hash: "
                    msg += f"{self.ext_hash} Downloaded Bytes: {tor_info.downloaded} "
                    msg += f"Size: {tor_info.size} Total Size: {tor_info.total_size}"
                    LOGGER.info(msg)
                    self.client.torrents_recheck(torrent_hashes=self.ext_hash)
                    self.__rechecked = True
                elif TORRENT_TIMEOUT is not None and time() - self.__stalled_time >= TORRENT_TIMEOUT:
                    self.onDownloadError("Dead Torrent!")
            elif tor_info.state == "missingFiles":
                self.client.torrents_recheck(torrent_hashes=self.ext_hash)
            elif (tor_info.state.lower().endswith("up") or tor_info.state == "uploading") and not self.uploaded:
                self.uploaded = True
                self.client.torrents_pause(torrent_hashes=self.ext_hash)
                if self.select:
                    clean_unwanted(self.path)
                self.__remove_torrent()
            elif tor_info.state == "error":
                self.onDownloadError("No enough space for this torrent on device")
        except Exception as e:
            LOGGER.error(str(e))

    def onDownloadError(self, message):
        LOGGER.info(f"Cancelling Download: {self.name}, cause: {message}")
        self.client.torrents_pause(torrent_hashes= self.ext_hash)
        sleep(0.3)
        self.__remove_torrent()

    def __remove_torrent(self):
        self.client.torrents_delete(torrent_hashes= self.ext_hash, delete_files=True)
        self.client.auth_log_out()
        self.periodic.cancel()

def _get_hash_magnet(mgt: str):
    hash_ = re_search(r'(?<=xt=urn:btih:)[a-zA-Z0-9]+', mgt).group(0)
    if len(hash_) == 32:
        hash_ = b16encode(b32decode(str(hash_))).decode()
    return str(hash_)

def _get_hash_file(path):
    with open(path, "rb") as f:
        decodedDict = bdecode(f.read())
        hash_ = sha1(bencode(decodedDict[b'info'])).hexdigest()
    return str(hash_)
       

