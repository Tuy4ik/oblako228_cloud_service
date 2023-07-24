import socket
import os


class User:
    def __init__(self):
        self.connection = None
        self.address = None
        self.username = None

    def connect(self, host_address='127.0.0.1', host_port=1415):
        host = socket.socket()
        host.bind((host_address, host_port))
        host.listen(1)
        conn, addr = host.accept()
        print("connection data:", conn, addr)
        self.connection = conn
        self.address = addr
        return conn, addr

    def log(self):
        while self.username is None:
            mode = self.connection.recv(2048).decode('utf-8')
            username = self.connection.recv(2048).decode('utf-8')
            password = self.connection.recv(2048).decode('utf-8')
            message = ""
            if mode == "enter":
                with open("user_data.txt", "r") as user_data:
                    lines_entering = user_data.readlines()
                    if "username: "+username+"\n" in lines_entering and "password: "+password+"\n" in lines_entering:
                        os.chdir("user_directories\\"+username)
                        message = "user authorised"
                    if "password: "+password+"\n" not in lines_entering:
                        message += "password incorrect "
                    if "username: "+username+"\n" not in lines_entering:
                        message += "username incorrect"
            elif mode == "register":
                with open("user_data.txt", "r") as read_user_data:
                    lines_registering = read_user_data.readlines()
                    if "password: "+password+"\n" not in lines_registering and "username: "+username+"\n" not in lines_registering:
                        os.mkdir("user_directories\\"+username)
                        with open("user_data.txt", "a") as write_user_data:
                            write_user_data.write("username: " + username + "\n" + "password: " + password + "\n")
                        os.chdir("user_directories\\"+username)
                        message = "user authorised"
                    if "password: "+password+"\n" in lines_registering:
                        message += "password already exists "
                    if "username: "+username+"\n" in lines_registering:
                        message += "username already exists"
            self.connection.send(message.encode('utf-8'))
            print(message)
            if message == "user authorised":
                self.username = username


    def delete(self, names_to_delete):
        if names_to_delete in os.listdir():
            if os.path.isfile(names_to_delete):
                os.remove(names_to_delete)
            elif os.path.isdir(names_to_delete):
                for root, dirnames, filenames in os.walk(os.getcwd() + "\\" + names_to_delete):
                    for i in filenames:
                        print("\\".join(root.split("\\")[root.split("\\").index(names_to_delete):]) + "\\" + i)
                        os.remove(root + "\\" + i)
                while len(os.listdir(names_to_delete)) > 0:
                    for root, dirnames, filenames in os.walk(os.getcwd() + "\\" + names_to_delete):
                        print(root)
                        try:
                            os.rmdir(root)
                        except:
                            pass
            return "complete"
        else:
            return "no such file or directory"

    def receive_file(self, upload_directory):
        for i in range(int(self.connection.recv(2048).decode('utf-8').strip())):
            file_name = self.connection.recv(2048).decode('utf-8').strip().split("\\")
            if len(file_name) > 1:
                for j in file_name[:-1]:
                    if j not in os.listdir():
                        os.mkdir(j)
                    os.chdir(j)
            with open(file_name[-1], "wb") as file_created:
                file_being_received_size = int(self.connection.recv(2048).decode('utf-8'))
                print(file_being_received_size)
                for k in range(file_being_received_size):
                    file_created.write(self.connection.recv(2048))
                file_created.write(self.connection.recv(int(self.connection.recv(2048).decode('utf-8'))))
            os.chdir(upload_directory)

    def send_file(self, file_to_send):
        file_size = os.path.getsize(file_to_send)//2048
        self.connection.send(str(file_size).rjust(2048, " ").encode('utf-8'))
        with open(file_to_send, "rb") as file_opened:
            for i in range(file_size):
                self.connection.send(file_opened.read(2048))
            print(str(os.path.getsize(file_to_send)-file_size*2048))
            self.connection.send(str(os.path.getsize(file_to_send)-file_size*2048).rjust(2048, "0").encode('utf-8'))
            self.connection.send(file_opened.read(os.path.getsize(file_to_send)-file_size*2048))

    def list(self):
        self.connection.send("\\".join(os.getcwd().split("\\")[os.getcwd().split("\\").index(self.username):]).ljust(2048, " ").encode('utf-8'))
        self.connection.send(str(len(os.listdir())).ljust(2048, " ").encode('utf-8'))
        for directory in os.listdir():
            self.connection.send(directory.ljust(2048, " ").encode('utf-8'))
            print("sent", directory)

    def satisfy_client_request(self):
        self.list()
        request = self.connection.recv(2048).decode('utf-8').split(" ", 1)
        print(request)
        match request:
            case "create", name_of_folder_to_create:
                os.mkdir(name_of_folder_to_create)
            case "goto", name_of_folder_to_goto:
                os.chdir(name_of_folder_to_goto)
            case "delete", name_to_delete:
                self.connection.send(self.delete(name_to_delete).encode('utf-8'))
            case "upload", name_to_upload:
                print("uploading")
                self.receive_file(os.getcwd())
            case "download", name_to_download:
                if name_to_download in os.listdir():
                    if os.path.isfile(name_to_download):
                        self.connection.send(b'1')
                        self.connection.send(name_to_download.ljust(2048, " ").encode('utf-8'))
                        self.send_file(name_to_download)
                    elif os.path.isdir(name_to_download):
                        number_of_files_to_send = 0
                        for root, dirs, filenames in os.walk(os.getcwd()+"\\"+name_to_download):
                            for i in filenames:
                                number_of_files_to_send += 1
                                print(i)
                        print(number_of_files_to_send, "files to send")
                        self.connection.send(str(number_of_files_to_send).encode('utf-8'))
                        for root, dirs, filenames in os.walk(os.getcwd()+"\\"+name_to_download):
                            for i in filenames:
                                os.chdir(root)
                                a = ("\\".join(root.split("\\")[root.split("\\").index(name_to_download):])+"\\"+i).ljust(2048, " ").encode('utf-8')
                                self.connection.send(a)
                                print(a)
                                self.send_file(i)
            case ["exit"]:
                pass
            case ['back']:
                os.chdir("\\".join(os.getcwd().split("\\")[:-1]))
                print("going back to "+"\\".join(os.getcwd().split("\\")[:-1]))


user = User()
user.connect()
user.log()
while True:
    user.satisfy_client_request()
