from bot.core.menus.menu_copy import copy_menu
from bot.core.varholderwrap import get_val, set_val
from bot.uploaders.rclone.rclone_copy import RcloneCopy


async def handle_setting_copy_menu_callback(callback_query):
    query= callback_query
    data = query.data.decode()
    cmd = data.split("^")
    message = await query.get_message()
    origin_drive = get_val("ORIGIN_DRIVE")
    origin_dir= get_val("ORIGIN_DIR")
    dest_drive= get_val("DESTINATION_DRIVE")
    dest_dir= get_val("DESTINATION_DIR")

    if query.data == "pages":
        await query.answer()

    #First Menu
    if cmd[1] == "list_drive_origin":
        set_val("ORIGIN_DRIVE", cmd[2])
        origin_drive= get_val("ORIGIN_DRIVE")
        await copy_menu(
            query= query, 
            message= message, 
            edit=True,
            msg= f'Select file or folder which you want to copy\n\nPath: `{origin_drive}`', 
            drive_name= origin_drive,
            submenu="list_dir", 
            data_cb="list_dir_origin",
            data_back_cb= "origin_menu_back",
            is_second_menu=False)

    elif cmd[1] == "list_dir_origin":
        path = get_val(cmd[2])
        origin_dir_= origin_dir + path + "/"
        set_val("ORIGIN_DIR", origin_dir_)
        await copy_menu(
             query,
             message, 
             edit=True, 
             msg=f"Select file or folder which you want to copy\n\nPath:`{origin_drive}:{origin_dir_}`", 
             drive_base= origin_dir_, 
             drive_name= origin_drive,
             submenu="list_dir",
             data_cb="list_dir_origin",
             data_back_cb="first_menu_back",
             is_second_menu= False)

    #Second Menu
    elif cmd[1] == "list_drive_second_menu":
        if cmd[3] == "True":
            path = get_val(cmd[2])
            rclone_dir= origin_dir + path + "/"
            set_val("ORIGIN_DIR", rclone_dir)    
        await copy_menu(
            query, 
            message, 
            edit=True, 
            msg=f'Select folder where you want to copy\n', 
            submenu="list_drive", 
            data_cb="list_drive_dest",
            is_second_menu=True)

    elif cmd[1] == "list_drive_dest":
        set_val("DESTINATION_DRIVE", cmd[2])
        dest_drive= get_val("DESTINATION_DRIVE")
        await copy_menu(
            query, 
            message, 
            edit=True, 
            msg=f'Select folder where you want to copy\n\nPath: `{dest_drive}`',
            drive_name= dest_drive,
            submenu="list_dir", 
            data_cb="list_dir_dest",
            data_back_cb= "dest_menu_back",
            is_second_menu=True)

    elif cmd[1] == "list_dir_dest":
        path = get_val(cmd[2])
        dest_dir_= dest_dir + path + "/"
        set_val("DESTINATION_DIR", dest_dir_)
        await copy_menu(
             query,
             message, 
             edit=True, 
             msg=f"Select folder where you want to copy\n\nPath:`{dest_drive}:{dest_dir_}`", 
             drive_name= dest_drive,
             drive_base= dest_dir_, 
             submenu="list_dir",
             data_cb="list_dir_dest",
             data_back_cb= "second_menu_back",
             is_second_menu= True)        
 
    elif cmd[1] == "start_copy":
        origin_dir_ = get_val("ORIGIN_DIR")
        origin_dir_= origin_dir_.split("/")[-2] + "/"
        set_val("DESTINATION_DIR", dest_dir + origin_dir_)
        rclone_copy= RcloneCopy(query)
        await rclone_copy.execute()

    elif cmd[1] == "selfdest":
        await query.answer("Closed")
        set_val("DESTINATION_DIR", "")
        set_val("DESTINATION_DRIVE","")
        set_val("ORIGIN_DIR", "")
        set_val("ORIGIN_DIR_DRIVE", "")
        await query.delete()

    #.........BACK BUTTONS HANDLING........#  

    # Origin Menu Back Button
    elif cmd[1] == "first_menu_back":
        data_back_cb= cmd[1]
        origin_dir= get_val("ORIGIN_DIR")
        origin_dir_list= origin_dir.split("/")[:-2]
        origin_dir_string = "" 
        for dir in origin_dir_list: 
            origin_dir_string += dir + "/"
        origin_dir= origin_dir_string
        set_val("ORIGIN_DIR", origin_dir_string)

        if origin_dir == "": data_back_cb= "origin_menu_back"

        await copy_menu(
             query,
             message, 
             edit=True, 
             msg=f"Select file or folder which you want to copy\n\nPath:`{origin_drive}:{origin_dir}`", 
             drive_base=origin_dir, 
             drive_name= origin_drive,
             submenu="list_dir",
             data_cb="list_dir_origin",
             data_back_cb= data_back_cb,
             is_second_menu= False)   
    
    elif cmd[1]== "origin_menu_back":
        await copy_menu(
            query, 
            message, 
            msg= "Select cloud where your files are stored",
            submenu= "list_drive",
            data_cb="list_drive_origin",
            edit=True)

    # Destination Menu Back Button
    elif cmd[1] == "second_menu_back":
        data_b_cb= cmd[1]
        dest_dir= get_val("DESTINATION_DIR")
        dest_dir_list= dest_dir.split("/")[:-2]
        dest_dir_string = "" 
        for dir in dest_dir_list: 
            dest_dir_string += dir + "/"
        dest_dir= dest_dir_string
        set_val("DESTINATION_DIR", dest_dir)
        
        if dest_dir == "": data_b_cb= "dest_menu_back"

        await copy_menu(
             query,
             message, 
             edit=True, 
             msg=f"Select folder where you want to copy\n\nPath:`{dest_drive}:{dest_dir}`", 
             drive_base= dest_dir, 
             drive_name= dest_drive,
             submenu="list_dir", 
             data_cb="list_dir_dest",
             data_back_cb= data_b_cb,
             is_second_menu= True)   

    elif cmd[1]== "dest_menu_back":
        await copy_menu(
            query, 
            message, 
            msg= f"Select cloud where to copy files", 
            submenu= "list_drive",
            data_cb="list_drive_dest",
            edit=True)          

                

