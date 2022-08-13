from bot.core.menus.menu_mirrorset import mirrorset_menu
from bot.core.varholderwrap import get_val, set_val


async def handle_setting_mirroset_callback(callback_query):
    data = callback_query.data.decode()
    cmd = data.split("^")
    message = await callback_query.get_message()
    base_dir= get_val("BASE_DIR")
    rclone_drive = get_val("RCLONE_DRIVE")

    if callback_query.data == "pages":
        await callback_query.answer()

    elif cmd[1] == "list_drive_mirrorset_menu":
        set_val("BASE_DIR", "")
        base_dir = get_val("BASE_DIR")
        set_val("RCLONE_DRIVE", cmd[2])
        await mirrorset_menu(
            callback_query, 
            message, 
            edit=True,
            msg=f"Select folder where you want to store files\n\nPath:`{cmd[2]}:{base_dir}`", 
            drive_name= cmd[2], 
            submenu="list_dir", 
            data_cb="list_dir_mirrorset_menu", 
            data_back_cb= "mirrorsetmenu"
            )     

    elif cmd[1] == "list_dir_mirrorset_menu":
        path = get_val(cmd[2])
        base_dir += path + "/"
        set_val("BASE_DIR", base_dir)
        await mirrorset_menu(
            callback_query, 
            message, 
            edit=True, 
            msg=f"Select folder where you want to store files\n\nPath:`{rclone_drive}:{base_dir}`", 
            drive_base=base_dir, 
            drive_name= rclone_drive, 
            submenu="list_dir", 
            data_cb="list_dir_mirrorset_menu", 
            data_back_cb= "back"
            )

    elif cmd[1] == "back":
        data_b_cb= ""
        base_dir= get_val("BASE_DIR")
        base_dir_split= base_dir.split("/")[:-2]
        base_dir_string = "" 
        for dir in base_dir_split: 
            base_dir_string += dir + "/"
        base_dir = base_dir_string
        set_val("BASE_DIR", base_dir)
        
        if base_dir == "": data_b_cb= "mirrorsetmenu"

        await mirrorset_menu(
            callback_query,
            message, 
            edit=True, 
            msg=f"Select folder where you want to store files\n\nPath:`{rclone_drive}:{base_dir}`", 
            drive_base=base_dir, 
            drive_name= rclone_drive, 
            submenu="list_dir", 
            data_cb="list_dir_mirrorset_menu", 
            data_back_cb= data_b_cb
            ) 

    elif cmd[1]== "mirrorsetmenu":
         await mirrorset_menu(
            callback_query, 
            message, 
            msg= f"Select cloud where you want to upload file\n\nPath:`{rclone_drive}:{base_dir}`",
            submenu="list_drive",
            edit=True)                

    elif cmd[1] == "selfdest":
        await callback_query.answer("Closed")
        await callback_query.delete()