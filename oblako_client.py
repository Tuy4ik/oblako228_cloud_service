import socket
import os

logging = "on"


def sendfile(filename):
    file_size_u = os.path.getsize(filename)
    s.send(bytes(str(file_size_u // 50).rjust(24, '0'), 'utf-8'))
    s.send(bytes(str(file_size_u % 50).rjust(24, '0'), 'utf-8'))
    file_opened = open(filename, "rb")
    while file_size_u > 0:
        if file_size_u > 50:
            data = file_opened.read(50)
            file_size_u -= 50
        else:
            data = file_opened.read(file_size_u)
            file_size_u = 0
        s.send(data)
    file_opened.close()


def receivefile(name_of_file):
    fileCreated = open(name_of_file, "wb")
    fileSizeD = int(s.recv(24).decode('utf-8'))
    fileSizeDR = int(s.recv(24).decode('utf-8'))
    for i in range(fileSizeD):
        fileCreated.write(s.recv(50))
    if fileSizeDR > 0:
        fileCreated.write(s.recv(fileSizeDR))
    fileCreated.close()


def view():
    s.send(b"view")
    amount = int(s.recv(16).decode("utf-8"))
    for a in range(amount):
        print(s.recv(84).decode("utf-8").strip())


def currentdir():
    s.send(b'cdir')
    print(s.recv(256).decode('utf-8').strip())    


accessStatus = "denied"
action = ""
amount = 0
fileSizeU = ""
filesizeD = ""
prevdir = ""
curdir = ""
mode = "manual"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 1415))

while accessStatus == "denied":
    print("напишите \"sign in\" для входа или \"sign up\" для регистрации")
    while True:
        optionChosen = input()
        if optionChosen == "sign in":
            s.send(b'0')
            break
        if optionChosen == "sign up":
            s.send(b'1')
            break
    username = input("username ").ljust(16, " ")
    password = input("password ").ljust(16, " ")
    s.send(bytes(username, 'utf-8'))
    s.send(bytes(password, 'utf-8'))
    if s.recv(8).decode('utf-8') == 'username':
        print("пользователь с таким именем уже существует")
    if s.recv(8).decode('utf-8') == 'password':
        print("пользователь с таким паролем уже существует")
    accessStatus = s.recv(6).decode("utf-8")
    if accessStatus == "denied":
        print("вы неверно ввели данные или произошла ошибка")
print("вы успешно вошли, \nhelp - список команд")
print(os.getcwd())
curdir = username

# действия клиента
while True:
    action = input()
    if action == "help":
        print("view - показать содержимое текущей папки\nlogging on/off - включить или выключить логирование\ndelete + имя папки - удалить выбранную папку со всем содержимым\nexit - выйти\nupload + название - загрузить файл\ndownload + название - скачать файл\ncreate + имя папки - создать папку с желаемым названием\ngoto + название - перейти в папку\nback - назад\ncurdir -текущая директория\nmode\n\tбез аргумента - узнать режим на данный момент\n\tmanual - режим по умолчанию\n\tauto - вызывать curdir и view после каждого действия")
    if action == "view":
        view()
    if action[:7] == "create ":
        s.send(b"crte")
        s.send(bytes(action[7:].ljust(84, " "), 'utf-8'))
    if action == "exit":
        s.send(b'exit')
        os._exit(os.X_OK)
    if action[:5] == "goto ":
        s.send(b"goto")
        s.send(bytes(action[5:].ljust(84, " "), 'utf-8'))
        prevdir = curdir
        curdir += action[5:]
    if action[:7] == "upload ":
        curdir = os.getcwd()
        numFiles = 0
        s.send(b"upld")
        fileName = action[7:].split("\\")[-1]
        fileStatus = os.path.isfile(fileName)
        if fileStatus:
            s.send(b'file')
            s.send(bytes(fileName.ljust(48, ' '), 'utf-8'))
            sendfile(fileName)
        else:
            s.send(b'fold')
            for root, dirnames, filenames in os.walk(action[7:]):
                for i in filenames:
                    numFiles += 1
            print(numFiles)
            s.send(bytes(str(numFiles).rjust(24, '0'), 'utf-8'))
            for root, dirnames, filenames in os.walk(action[7:]):
                for i in filenames:
                    s.send(bytes("\\".join(root.split("\\")[root.split("\\").index(fileName):]).ljust(432, " "), 'utf-8'))
                    s.send(bytes(i.ljust(84), 'utf-8'))
                    os.chdir(root)
                    sendfile(i)
                    os.chdir(curdir)
        print("uploading complete")
    if action[:9] == "download ":
        s.send(b"dnld")
        s.send(bytes(action[9:].ljust(48, " "), 'utf-8'))
        if s.recv(6).decode('utf-8') == "doesnt":
            print("в выбранной директории нет файла с таким названием")
        else:
            print("введите путь для загрузки, 0 для выбора текущей директории")
            path = input()
            if path == "0":
                path = os.getcwd()
            os.chdir(path)
            if os.path.isfile(action[9:]):
                receivefile(action[9:])
            else:
                numberOfFilesDownloading = int(s.recv(24).decode('utf-8'))
                for i in range(numberOfFilesDownloading):
                    for j in s.recv(432).decode('utf-8').strip().split("\\"):
                        if j not in os.listdir():
                            os.mkdir(j)
                        os.chdir(j)
                    receivefile(s.recv(84).decode('utf-8').strip())
                    os.chdir(path)
                    if logging == "on":
                        print(str(i+1)+"/"+str(numberOfFilesDownloading))
        print("download complete")
    if action == "back":
        s.send(b"back")
    if action == "curdir":
        currentdir()
    if action == "mode auto":
        mode = "auto"
    if action == "mode manual":
        mode = "manual"
    if action == "mode":
        print(mode)
    if action == "logging on":
        s.send(b'lgon')
    if action == "logging off":
        s.send(b'loff')
    if action[:7] == "delete ":
        s.send(b'delt')
        s.send(action[7:].ljust(256, ' ').encode('utf-8'))
        if s.recv(6).decode('utf-8') == 'doesnt':
            print("в текущей директории нет папки с указанным именем")
    if mode == "auto":
        currentdir()
        view()
