import os
from shutil import rmtree
from bot import BASE_URL, DOWNLOAD_DIR, LOGGER, WEB_PINCODE, aria2, get_client, status_dict
from itertools import zip_longest
from json import loads as jsnloads
import os
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telethon.tl.types import KeyboardButtonCallback
from subprocess import check_output
from subprocess import check_output
from json import loads

ARCH_EXT = [".tar.bz2", ".tar.gz", ".bz2", ".gz", ".tar.xz", ".tar", ".tbz2", ".tgz", ".lzma2",
                ".zip", ".7z", ".z", ".rar", ".iso", ".wim", ".cab", ".apm", ".arj", ".chm",
                ".cpio", ".cramfs", ".deb", ".dmg", ".fat", ".hfs", ".lzh", ".lzma", ".mbr",
                ".msi", ".mslz", ".nsis", ".ntfs", ".rpm", ".squashfs", ".udf", ".vhd", ".xar"]

ZIP_EXT = (".zip", ".7z", ".gzip2", ".iso", ".wim", ".rar")

def pairwise(iterable):
    "s -> (s0, s1), (s2, s3), (s4, s5), ..."
    a = iter(iterable)
    return zip_longest(a, a)

def clean(path):
    LOGGER.info(f"Cleaning Download: {path}")
    try:
        rmtree(path)
    except:
        os.remove(path)

def clean_all():
    aria2.remove_all(True)
    get_client().torrents_delete(torrent_hashes="all")
    try:
        rmtree(DOWNLOAD_DIR)
    except:
        pass

def start_cleanup():
    try:
        rmtree(DOWNLOAD_DIR)
    except:
        pass
    os.makedirs(DOWNLOAD_DIR)

def rename_file(old_path, new_name):
    pathname, ext = os.path.splitext(old_path)
    new_name= new_name + ext
    new_path= f'{DOWNLOAD_DIR}{new_name}'
    os.rename(old_path, new_path)
    return new_path

def get_rclone_config():
    rclone_conf = os.path.join(os.getcwd(), 'rclone.conf')
    if rclone_conf is not None:
        if isinstance(rclone_conf, str):
            if os.path.exists(rclone_conf):
                return rclone_conf
    return None

def get_readable_size(size):
    """Get size in readable format"""

    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i]) 

def get_media_info(path):
    try:
        result = check_output(["ffprobe", "-hide_banner", "-loglevel", "error", "-print_format",
                                            "json", "-show_format", path]).decode('utf-8')
        fields = loads(result)['format']
    except Exception as e:
        LOGGER.error(f"get_media_info: {e}")
        return 0, None, None
    try:
        duration = round(float(fields['duration']))
    except:
        duration = 0
    try:
        artist = str(fields['tags']['artist'])
    except:
        artist = None
    try:
        title = str(fields['tags']['title'])
    except:
        title = None
    return duration, artist, title

def get_video_resolution(path):
    try:
        result = check_output(["ffprobe", "-hide_banner", "-loglevel", "error", "-select_streams", "v:0",
                                          "-show_entries", "stream=width,height", "-of", "json", path]).decode('utf-8')
        fields = jsnloads(result)['streams'][0]

        width = int(fields['width'])
        height = int(fields['height'])
        return width, height
    except Exception as e:
        LOGGER.error(f"get_video_resolution: {e}")
        return 480, 320


def bt_selection_buttons(id_: str):
    if len(id_) > 20:
        gid = id_[:12]
    else:
        gid = id_

    pincode = ""
    for n in id_:
        if n.isdigit():
            pincode += str(n)
        if len(pincode) == 4:
            break

    buttons = ButtonMaker()
    if WEB_PINCODE:
        buttons.url_buildbutton("Select Files", f"{BASE_URL}/app/files/{id_}")
        buttons.cb_buildbutton("Pincode", f"btsel pin {gid} {pincode}")
    else:
        buttons.url_buildbutton("Select Files", f"{BASE_URL}/app/files/{id_}?pin_code={pincode}")
    buttons.cb_buildbutton("Done Selecting", f"btsel done {gid} {id_}")
    return InlineKeyboardMarkup(buttons.build_menu(2))

def getDownloadByGid(gid):
    for dl in list(status_dict.values()):
        if dl.gid() == gid:
            return dl
    return None

class ButtonMaker:
    def __init__(self):
        self.first_button = []
        self.second_button= []

    def url_buildbutton(self, key, link):
        self.first_button.append(InlineKeyboardButton(text = key, url = link))

    def cb_buildbutton(self, key, data):
        self.first_button.append(InlineKeyboardButton(text = key, callback_data = data))

    def cbl_buildbutton(self, key, data):
        self.first_button.append([InlineKeyboardButton(text = key, callback_data = data)])

    def ap_buildbutton(self, data):
        self.first_button.append(data)

    def cb_buildsecbutton(self, key, data):
        self.second_button.append(InlineKeyboardButton(text = key, callback_data = data))

    def dbuildbutton(self, first_text, first_callback, second_text, second_callback):
        self.first_button.append([InlineKeyboardButton(text = first_text, callback_data = first_callback), 
                            InlineKeyboardButton(text = second_text, callback_data = second_callback)])
    
    def tbuildbutton(self, first_text, first_callback, second_text, second_callback, third_text, third_callback):
        self.first_button.append([InlineKeyboardButton(text = first_text, callback_data = first_callback), 
                    InlineKeyboardButton(text = second_text, callback_data = second_callback),
                    InlineKeyboardButton(text = third_text, callback_data = third_callback)])

    def build_menu(self, n_cols):
        menu = [self.first_button[i:i + n_cols] for i in range(0, len(self.first_button), n_cols)]
        return menu

class TelethonButtonMaker:
    def __init__(self):
        self.first_button = []
        self.second_button= []

    def cb_buildbutton(self, key, data):
        self.first_button.append(KeyboardButtonCallback(text = key, data = data))

    def cbl_buildbutton(self, key, data):
        self.first_button.append([KeyboardButtonCallback(text = key, data = data)])

    def ap_buildbutton(self, data):
        self.first_button.append(data)

    def cb_buildsecbutton(self, key, data):
        self.second_button.append(KeyboardButtonCallback(text = key, data = data))

    def dbuildbutton(self, first_text, first_callback, second_text, second_callback):
        self.first_button.append([KeyboardButtonCallback(text = first_text, data = first_callback), 
                            KeyboardButtonCallback(text = second_text, data = second_callback)])

    def tbuildbutton(self, first_text, first_callback, second_text, second_callback, third_text, third_callback):
        self.first_button.append([KeyboardButtonCallback(text = first_text, data = first_callback), 
                                KeyboardButtonCallback(text = second_text, data = second_callback),
                                KeyboardButtonCallback(text = third_text, data = third_callback)])

    def build_menu(self, n_cols):
        menu = [self.first_button[i:i + n_cols] for i in range(0, len(self.first_button), n_cols)]
        return menu



