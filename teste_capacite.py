import random
import sys
import hashlib
import json
from os.path import exists
import os
import sqlite3
import time
import shutil
from termcolor import colored
import datetime
import signal

if os.name == 'nt':
    import wmi

def handler(signum, frame):
    global total_file_size,total_file_size_without_error,time_for_execute,cpt_error

    print (f"time to execute {datetime.timedelta(seconds=time.time() - time_for_execute)}")
    if total_file_size != total_file_size_without_error:
        color_display = "red"
    else:
        color_display = "green"
    print(f" {return_size(total_file_size)} have been copied and {colored(return_size(total_file_size_without_error), color_display)} without error")

    if cpt_error >0:
        print (colored (f'{cpt_error} error have been detected on check or during copy','red'))

    sys.exit(2)

def return_hash(file_name,size_buffer,type_hash):

    if type_hash == "sha1":
        hash = hashlib.sha1()
    elif type_hash == "sha256":
        hash = hashlib.sha256()
    elif type_hash == "sha512":
        hash = hashlib.sha512()
    else:
        hash = hashlib.md5()

    with open(file_name, "rb") as f:
        for chunk in iter(lambda: f.read(size_buffer), b""):
            hash.update(chunk)
    return hash.hexdigest()

def insert_table(table,fields,values,cur,conn):
    query = f"""INSERT INTO {table} ({fields}) VALUES ({values})"""

    try:
        cur.execute(query)
        conn.commit()
        return True
    except:
        return False

def get_id():
    return f"id_{random.randrange(1,100000)}"

def select_table(table, fields,disk_serial,cpt_nb_recheck,session_id,cur):

    query = f"""SELECT {fields} FROM {table} WHERE serial_disk like '{disk_serial}' AND id_session like '{session_id}' ORDER BY filename LIMIT {cpt_nb_recheck}"""
    cur.execute(query)
    rows = cur.fetchall()
    return rows

def is_db_exist(filename):
    return exists(filename)

def create_db(filename):
    cur,conn = open_db(filename)
    query = """ CREATE TABLE  "check_file"("serial_disk" TEXT, "id_session" TEXT, "filename" TEXT, "hash_host" TEXT, "hash_move" TEXT, "time_copy_dest" INTEGER, "time_copy_back" INTEGER, "space_free" INTEGER, "size_file" TEXT) """
    cur.execute(query)

def open_config():
    with open("config.json", "r") as fp:
        return json.load(fp)

def open_db(filename):
    conn = sqlite3.connect(filename)
    return conn.cursor(),conn

def return_serial(disk):
    if os.name == "nt":
        new_wmi = wmi.WMI()
        logical_disk = new_wmi.Win32_LogicalDisk(Caption=disk)[0]
        return logical_disk.VolumeSerialNumber
    else:
        print ("todo")
        sys.exit(1)

def return_size_file(size_file, variation):
    if variation==0:
        return size_file
    if random.randrange(0,2) == 1:
        return size_file * (1 + (random.randrange(0,variation+1)/100))
    return size_file * (1 - (random.randrange(0, variation + 1) / 100))

def create_file(size_file,is_random,if_no_random,variation):
    name_file = str(time.time()).replace('.',"-")
    size_file = int (return_size_file(size_file,variation))

    try:
        with open(name_file, "wb") as fp:
            if is_random:
                fp.write(os.urandom(size_file))
            else:
                fp.write(if_no_random.encode() * int(size_file/len(if_no_random)))
        return  True, size_file, name_file
    except:
        return False, size_file, name_file

def return_used_space(hard_drive):
    stat_hard_drive = shutil.disk_usage(hard_drive)
    return  int ((stat_hard_drive.free/stat_hard_drive.total) * 100)

def return_size(size):
    if size > 1000000000000:
        return  "{:.2f} TB".format(size/1000000000000)
    elif size > 1000000000:
        return  "{:.2f} GB".format((size/1000000000))
    elif size > 1000000:
        return  "{:.2f} MB".format((size/1000000))
    elif size > 1000:
        return  "{:.2f} Kb".format((size/1000))
    else:
        return "{} bytes".format((size))


total_file_size=0
total_file_size_without_error = 0
cpt_error = 0
time_for_execute = 0

def main():
    global total_file_size, total_file_size_without_error, time_for_execute, cpt_error

    if len(sys.argv) != 2:
        print ("please add name of your target disk : 'd:' for Windows or '/media/d' for Linux")
        sys.exit(1)

    signal.signal(signal.SIGINT, handler)
    hard_drive = sys.argv[1]
    config = open_config()
    nb_recheck = config["recheck"]
    cpt_recheck = nb_recheck
    cpt_nb_recheck=1
    id_session = get_id()

    if not is_db_exist(config["db_name"]):
        create_db(config["db_name"])

    cur,conn = open_db(config["db_name"])
    disk_serial = return_serial(hard_drive).strip()
    time_for_execute=time.time()
    while True:
        is_file_created,size_file, name_of_file = create_file(config["size_file"],config["random"], config["if_no_random"], config["pourcentage_of_variation"])
        total_file_size += size_file
        if not is_file_created:
            print ("end")
            sys.exit(1)
        original_hash = return_hash(name_of_file,config['buffer_hash'],config["hash_type"])
        time_before_copy = time.time()
        print(colored("copy from host to hard drive", "blue"))
        try:
            shutil.move( name_of_file, f"{hard_drive}\\{name_of_file}")
        except Exception as e:
            os.remove(name_of_file)
            break

        time_to_copy = "{:.2f}".format(time.time() - time_before_copy)
        after_copy_hash = return_hash(f"{hard_drive}\\{name_of_file}",config['buffer_hash'],config["hash_type"])
        space_used = return_used_space(hard_drive)
        if original_hash != after_copy_hash:
            color_display = "red"
            cpt_error += 1
        else:
            total_file_size_without_error+=size_file
            color_display = "green"
        print (f"file {name_of_file} : original hash {colored (original_hash,color_display)}, hash after copy {colored (after_copy_hash,color_display)}. {time_to_copy} seconds to copy")
        if total_file_size != total_file_size_without_error:
            color_display = "red"
        else:
            color_display ="green"
        print (f"{space_used}% of free space. {return_size(total_file_size)} copied and {colored(return_size(total_file_size_without_error),color_display)} without error")

        time_to_copy_back = 0
        if config["check_back"]:
            time_before_copy = time.time()
            print (colored ("copy from hard drive to host","blue"))
            shutil.copy(f"{hard_drive}\\{name_of_file}",name_of_file)
            copy_back_hash = return_hash(name_of_file, config['buffer_hash'], config["hash_type"])
            os.remove(name_of_file)
            if original_hash != copy_back_hash:
                color_display = "red"
                cpt_error += 1
            else:
                color_display = "green"
            time_to_copy_back = "{:.2f}".format(time.time() - time_before_copy)
            print(
                f"file {name_of_file} : original hash {colored(original_hash, color_display)}, hash after copy {colored(copy_back_hash, color_display)}. {time_to_copy_back} seconds to copy back")

        insert_table("check_file","serial_disk,id_session, filename,hash_host,hash_move,time_copy_dest, time_copy_back, size_file,space_free", f"'{disk_serial}','{id_session}','{name_of_file}','{original_hash}','{after_copy_hash}','{time_to_copy}','{time_to_copy_back}','{return_size(size_file)}',{space_used}",cur, conn)

        if cpt_recheck != 0:
            cpt_recheck -= 1
        else:
            cpt_recheck =nb_recheck
            print (colored (f"recheck of {cpt_nb_recheck} file(s) ","blue"))
            file_to_recheck = select_table("check_file","filename,hash_host",disk_serial,cpt_nb_recheck,id_session, cur)
            cpt_nb_recheck += 1
            for tupple_file in file_to_recheck:
                hash_recheck = return_hash(f"{hard_drive}\\{tupple_file[0]}", config['buffer_hash'],config["hash_type"])
                if hash_recheck != tupple_file[1]:
                    cpt_error +=1
                    print (f"for file {tupple_file[0]} {colored ('hash is different','red')} {tupple_file[1]} for original file and {hash_recheck}")
                else:
                    print(f"for file {tupple_file[0]} {colored('hash is the same', 'green')} ")
        if cpt_error >= config["end_after_x_error"]  :
            print (colored ("this program has been stopped because to number of errors reached ","red"))
            break

    handler(signal.SIGINT,"")

if __name__ == "__main__":
    main()
