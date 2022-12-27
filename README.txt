This script is to test capacity, real or supposed, of one hard drive ( especially hard drive you can find on aliexpress, you know a 64T for 30€) 


This script will do 
- retrieve serial number of this disk
- create a file on the host with size defined on the config file. Size could be each time same but could be with variation defined on the config file. each byte could be random (to avoid compression)  or a string retrieved from the config file
- make a hash of this file
- put hash and filename on a DB
- move this file to the target hard drive 
- calculate time for this move and insert it in the DB
- calculate free space, supposed, on the target drive and it is inserted on the DB
- make a hash of the file moved on the target, insert this hash on DB and display result. If it is different, it will be red
- every X filed created ( value on the config file), first file created is hashed again.  First time, it is one file, second time 2 files, ....... if orginal hash  is different of the hash done after this "recheck", a error message will be displayed 
- when disk is full or if number or errors is reached, script 'll stop. if needed, an error message will be displayed 

another option allows to make a copy from target to host, hash this file and check if it is same as orginal 


DB will be created on the first run of this script


On DB 
- Serial of the disk
- ID session
- filename
- hash from original file
- hash after move
- to to copy
- time to copy bask
- free space after move
- size of the file ( with or without variation


config file 
```

{
	"db_name":"check_disk.db", #name of DB
	"size_file":1000000000, # size of the file in byte
	"pourcentage_of_variation":0, # % of variation. if 0, there is no variation
	"buffer_hash":65536, # value of the buffer for hash 
	"random":true, # file filled with random byte or not 
	"if_no_random":"ABCDE", # if it is no random, file will be filled with a char or a string
	"recheck":10, # make a recheck after x files
	"end_after_x_error":5, # stop script after X errors
	"check_back":false, # check from target to host
	"hash_type":"md5" # type of hash  md5, sha1, sha256 or sha512
}
```

