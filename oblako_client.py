import socket
import os
import random

script_directory = os.getcwd()


class Client:
    def __init__(self):
        self.username = None
        self.authorisation_status = None
        self.connection = None

    def connect(self, host_address='127.0.0.1', host_port=1415):
        self.connection = socket.socket()
        self.connection.connect((host_address, host_port))
        print("connected")

    def log(self):
        while self.authorisation_status != "user authorised":
            mode = input("enter \"enter\" to sign in or \"register\" to sign up: ")
            if mode == "enter" or mode == "register":
                self.connection.send(mode.encode('utf-8'))
            else:
                continue
            self.connection.send(input("username: ").encode('utf-8'))
            self.connection.send(input("password: ").encode('utf-8'))
            self.authorisation_status = self.connection.recv(2048).decode('utf-8')
            print(self.authorisation_status)

    def send_file(self, file_to_send):
        file_size = os.path.getsize(file_to_send) // 2048
        self.connection.send(str(file_size).rjust(2048, " ").encode('utf-8'))
        with open(file_to_send, "rb") as file_opened:
            for i in range(file_size):
                self.connection.send((int.from_bytes(file_opened.read(2048), 'big') ^ int.from_bytes(key, 'big')).to_bytes(2048, 'big'))
            print(str(os.path.getsize(file_to_send) - file_size * 2048))
            self.connection.send(str(os.path.getsize(file_to_send) - file_size * 2048).rjust(2048, "0").encode('utf-8'))
            self.connection.send(file_opened.read(os.path.getsize(file_to_send) - file_size * 2048))

    def receive_file(self, download_directory):
        os.chdir(script_directory)
        for i in range(int(self.connection.recv(2048).decode('utf-8').strip())):
            file_name = self.connection.recv(2048).decode('utf-8').strip().split("\\")
            if len(file_name) > 1:
                for j in file_name[:-1]:
                    if j not in os.listdir():
                        os.mkdir(j)
                    os.chdir(j)
            with open(file_name[-1], "wb") as file_created:
                file_being_received_size = int(self.connection.recv(2048).decode('utf-8'))
                for q in range(file_being_received_size):
                    file_created.write((int.from_bytes(self.connection.recv(2048), 'big') ^ int.from_bytes(key, 'big')).to_bytes(2048, 'big'))
                file_created.write(self.connection.recv(int(self.connection.recv(2048).decode('utf-8'))))
            os.chdir(download_directory)

    def request(self):
        print(self.connection.recv(2048).decode('utf-8').strip())
        for i in range(int(self.connection.recv(2048).decode('utf-8').strip())):
            print(self.connection.recv(2048).decode('utf-8').strip())
        action = input()
        self.connection.send(action.encode('utf-8'))
        match(action.split(" ", 1)):
            case "download", name_to_download:
                self.receive_file(os.getcwd())
            case "upload", name_to_upload:
                if name_to_upload in os.listdir():
                    if os.path.isfile(name_to_upload):
                        self.connection.send(b'1')
                        self.connection.send(name_to_upload.ljust(2048, " ").encode('utf-8'))
                        self.send_file(name_to_upload)
                    elif os.path.isdir(name_to_upload):
                        number_of_files_to_send = 0
                        for root, dirs, filenames in os.walk(os.getcwd() + "\\" + name_to_upload):
                            for k in filenames:
                                number_of_files_to_send += 1
                        self.connection.send(str(number_of_files_to_send).encode('utf-8'))
                        for root, dirs, filenames in os.walk(os.getcwd() + "\\" + name_to_upload):
                            for i in filenames:
                                os.chdir(root)
                                a = ("\\".join(root.split("\\")[root.split("\\").index(name_to_upload):]) + "\\" + i).ljust(
                                    2048, " ").encode('utf-8')
                                self.connection.send(a)
                                self.send_file(i)
            case ["exit"]:
                pass


if "client_password.txt" not in os.listdir():
    with open("client_password.txt", "ab") as creating_password_file:
        for i in range(64):
            creating_password_file.write(random.randint(0, 2147483647).to_bytes(32, 'big'))
with open("client_password.txt", "rb") as key_file:
    key = key_file.read(2048)
client = Client()
client.connect()
client.log()
while True:
    client.request()
