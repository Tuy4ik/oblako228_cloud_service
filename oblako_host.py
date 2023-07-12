import os
import socket

homedir = os.getcwd()
log = "on"


def sendfile(filename, conn):
    filesize = os.path.getsize(filename)
    conn.send(bytes(str(filesize // 50).rjust(24, '0'), 'utf-8'))
    conn.send(bytes(str(filesize % 50).rjust(24, '0'), 'utf-8'))
    fileopened = open(filename, "rb")
    while filesize > 0:
        if filesize > 50:
            data = fileopened.read(50)
            filesize -= 50
        else:
            data = fileopened.read(filesize)
            filesize = 0
        conn.send(data)
    fileopened.close()


def receivefile(filename, conn):
    fileSizeU = int(conn.recv(24).decode('utf-8'))
    fileSizeUR = int(conn.recv(24).decode('utf-8'))
    file_created = open(filename, "wb")
    for i in range(fileSizeU):
        file_created.write(conn.recv(50))
    if fileSizeUR > 0:
        file_created.write(conn.recv(fileSizeUR))
    file_created.close()


def connect():
    host = socket.socket()
    host.bind(('127.0.0.1', 1415))
    host.listen(1)
    conn, addr = host.accept()
    print("connection data:",conn, addr)
    return conn, addr


def hosting(logging):
    conn, addr = connect()

    access_obtained_user = ""

    while access_obtained_user == "":
        unique_user = True
        sign_or_enter = int(conn.recv(1))
        if sign_or_enter == 1:
            print("the user is signing up")
            username = conn.recv(16).decode("utf-8").strip()
            password = conn.recv(16).decode("utf-8").strip()
            with open(homedir + "\\user_data.txt", "r") as check:
                lines = check.readlines()
                if "user: " + username + "\n" in lines:
                    conn.send(b'username')
                    print("username already taken")  
                    unique_user = False
                else:
                    conn.send(b'00000000')
                if "password: " + password + "\n" in lines:
                    conn.send(b'password')
                    print("password already taken") 
                    unique_user = False
                else:
                    conn.send(b'00000000')
            print("the user is unique: "+unique_user)
            if unique_user:
                write = open(homedir + "\\user_data.txt", "a")
                print("user: " + username + "\\n")
                print("password: " + password + "\\n")
                write.write("user: " + username + "\n" + "password: " + password + "\n")
                write.close()
                read = open(homedir + "\\user_data.txt", "r")
                lines = read.readlines()
                print(lines)
                os.makedirs("user_directories\\" + username)
                access_obtained_user = username
                conn.send(b'signed')
            else:
                conn.send(b'denied')
        else:
            print("the user is signing in")
            read = open(homedir + "\\user_data.txt", "r")
            username = conn.recv(16).decode("utf-8").strip()
            password = conn.recv(16).decode("utf-8").strip()
            conn.send(b'00000000')
            conn.send(b'00000000')
            lines = read.readlines()
            print(lines)
            print("user: " + username + "\\n")  #
            print("password: " + password + "\\n")  #
            if ("user: " + username + "\n") in lines:  #
                print("the username received exists")  #
            if ("password: " + password + "\n") in lines:  #
                print("the password received exists")  #
            if (("user: " + username + "\n") in lines) and (("password: " + password + "\n") in lines):
                access_obtained_user = username
                conn.send(b'signed')
            else:
                conn.send(b'denied')
            read.close()
    access_obtained_user = access_obtained_user.strip()
    print("the username of a user that obtained acces:", access_obtained_user, "0")
    os.chdir("user_directories//" + access_obtained_user)
    print(os.getcwd())

    while True:
        action = conn.recv(4).decode("utf-8")
        if action == "view":
            conn.send(bytes(str(len(os.listdir())).rjust(16, "0"), 'utf-8'))
            for name in os.listdir():
                currentName = name.ljust(84, " ")
                conn.send(bytes(currentName, 'utf-8'))
        if action == "crte":
            nameOfFolderCreated = conn.recv(84).decode('utf-8').strip()
            os.mkdir(nameOfFolderCreated)
        if action == "goto":
            nameOfFolderGoTo = conn.recv(84).decode('utf-8').strip()
            os.chdir(nameOfFolderGoTo)
        if action == "upld":
            curdirU = os.getcwd()
            status = conn.recv(4).decode('utf-8')
            if status == 'file':
                print('user is uploading file')
                receivefile(conn.recv(48).decode('utf-8').strip(), conn)
            else:
                print('user is uploading folder')
                numberF = int(conn.recv(24).decode('utf-8'))
                print(numberF)
                for i in range(numberF):
                    for j in conn.recv(432).decode('utf-8').strip().split("\\"):
                        if j not in os.listdir():
                            os.mkdir(j)
                        os.chdir(j)
                    receivefile(conn.recv(84).decode('utf-8').strip(), conn)
                    os.chdir(curdirU)
        if action == "dnld":
            curdirD = os.getcwd()
            numFiles = 0
            fileName = conn.recv(48).decode('utf-8').strip()
            if fileName in os.listdir():
                conn.send(b"exists")
            else:
                conn.send(b"doesnt")
            if not os.path.isdir(fileName):
                sendfile(fileName, conn)
            else:
                for root, dirs, filenames in os.walk(os.getcwd() + "\\" + fileName):
                    for i in filenames:
                        if logging == "on":
                            print("\\".join(root.split("\\")[root.split("\\").index(fileName):]) + "\\" + i)
                            print(numFiles)
                        numFiles += 1
                conn.send(bytes(str(numFiles).rjust(24, '0'), 'utf-8'))
                for root, dirs, filenames in os.walk(os.getcwd() + "\\" + fileName):
                    for i in filenames:
                        if logging == "on":
                            print("\\".join(root.split("\\")[root.split("\\").index(fileName):]) + "\\" + i)
                        conn.send(bytes("\\".join(root.split("\\")[root.split("\\").index(fileName):]).ljust(432, " "),
                                        'utf-8'))
                        conn.send(bytes(i.ljust(84), 'utf-8'))
                        os.chdir(root)
                        sendfile(i, conn)
                        os.chdir(curdirD)
        if action == "back":
            if os.getcwd().split("\\")[-1] != access_obtained_user:
                os.chdir("\\".join(os.getcwd().split("\\")[:-1]))
        if action == "cdir":
            conn.send(bytes(
                "\\".join(os.getcwd().split("\\")[os.getcwd().split("\\").index(access_obtained_user):]).ljust(256, ' '),
                'utf-8'))
        if action == "delt":
            toDeleteName = conn.recv(256).decode('utf-8').strip()
            if toDeleteName in os.listdir():
                conn.send(b'exists')
                if os.path.isfile(toDeleteName):
                    os.remove(toDeleteName)
                else:
                    for root, dirnames, filenames in os.walk(os.getcwd() + "\\" + toDeleteName):
                        for i in filenames:
                            if logging == "on":
                                print("\\".join(root.split("\\")[root.split("\\").index(toDeleteName):]) + "\\" + i)
                            os.remove(root + "\\" + i)
                    print("files deleted")
                    while len(os.listdir(toDeleteName)) > 0:
                        for root, dirnames, filenames in os.walk(os.getcwd() + "\\" + toDeleteName):
                            if logging == "on":
                                print(root)
                            try:
                                os.rmdir(root)
                            except:
                                pass
                    os.rmdir(toDeleteName)
            else:
                conn.send(b'doesnt')
        if action == 'exit':
            conn.close()
            print("connection aborted")
            break
        if action == 'lgon':
            logging = "on"
            print("logging on")
        if action == 'loff':
            logging = "off"
            print("logging off")


if "user_directories" not in os.listdir():
    os.makedirs("user_directories")
if "user_data.txt" not in os.listdir():
    a = open("user_data.txt", "x")
    a.close()


while True:
    hosting(log)
    os.chdir(homedir)
