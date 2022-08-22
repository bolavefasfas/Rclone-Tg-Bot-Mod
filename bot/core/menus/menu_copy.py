import os, configparser
import asyncio
from json import loads as jsonloads
from bot.core.varholderwrap import set_val
from bot.utils.bot_utils.menu_utils import Menus, rcloneListButtonMaker
from bot.utils.bot_utils.misc_utils import TelethonButtonMaker, get_rclone_config, pairwise

folder_icon= "📁"

async def copy_menu(
    query, 
    message="",
    msg="", 
    submenu="", 
    drive_base="", 
    drive_name="", 
    data_cb="", 
    data_back_cb="",
    edit=False,
    is_second_menu= False, 
    ):
    
    buttons = TelethonButtonMaker()

    if submenu == "list_drive":
        path= os.path.join(os.getcwd(), "rclone.conf")
        conf = configparser.ConfigParser()
        conf.read(path)

        for j in conf.sections():
            if "team_drive" in list(conf[j]):
                buttons.cb_buildsecbutton(f"{folder_icon} {j}", f"copymenu^{data_cb}^{j}")
            else:
                buttons.cb_buildsecbutton(f"{folder_icon} {j}", f"copymenu^{data_cb}^{j}")
        
        for a, b in pairwise(buttons.second_button):
            row= [] 
            if b == None:
                row.append(a)  
                buttons.ap_buildbutton(row)
                break
            row.append(a)
            row.append(b)
            buttons.ap_buildbutton(row)


        buttons.cbl_buildbutton("✘ Close Menu", f"copymenu^selfdest")

        if edit:
            await message.edit(msg, buttons= buttons.first_button)
        else:
            await query.reply(msg, buttons= buttons.first_button)

    elif submenu == "list_dir":
        conf_path = get_rclone_config()

        if is_second_menu:
            buttons.cbl_buildbutton(f"✅ Select this folder", f"copymenu^start_copy")
        else:
            buttons.cbl_buildbutton(f"✅ Select this folder", f"copymenu^list_drive_second_menu^_^False")
        
        if is_second_menu:
            cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--dirs-only"] 
        else:
            cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}"] 

        process = await asyncio.create_subprocess_exec(*cmd, 
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
        )

        out, err = await process.communicate()
        out = out.decode().strip()
        return_code = await process.wait()

        if return_code != 0:
           err = err.decode().strip()
           return await message.reply(f'Error: {err}')  

        list_info = jsonloads(out)
        if is_second_menu:
            list_info.sort(key=lambda x: x["Name"]) 
        else:
            list_info.sort(key=lambda x: x["Size"])  
        set_val("list_info", list_info) 

        if len(list_info) == 0:
            buttons.cbl_buildbutton("❌Nothing to show❌", data="copymenu^pages")
        else:
            total = len(list_info)
            max_results= 10
            offset= 0
            start = offset
            end = max_results + start
            next_offset = offset + max_results

            if end > total:
                list_info= list_info[offset:]    
            elif offset >= total:
                list_info= []    
            else:
                list_info= list_info[start:end] 
        
            rcloneListButtonMaker(result_list=list_info, 
                buttons= buttons, 
                menu_type = Menus.COPY,
                callback= data_cb,
                is_second_menu = is_second_menu 
             )

            if offset == 0 and total <= 10:
                buttons.cbl_buildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", "copymenu^pages") 
            else: 
                buttons.dbuildbutton(f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", "copymenu^pages",
                                    "NEXT ⏩", f"n_copy {next_offset} {is_second_menu} {data_back_cb}")

        buttons.cbl_buildbutton("⬅️ Back", f"copymenu^{data_back_cb}")
        buttons.cbl_buildbutton("✘ Close Menu", "copymenu^selfdest")

        if edit:
            await message.edit(msg, buttons=buttons.first_button)
        else:
            await query.reply(msg, buttons=buttons.first_button)