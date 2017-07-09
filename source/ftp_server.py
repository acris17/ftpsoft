#imports
import argparse
import os
import sys
import threading
from socket import *

#class definitions
class Server:
    def __init__(self):
        """
        goal: define class properties
        type: (self) -> ()
        """

        #socket variables
        self.server_name     = ""
        self.server_port     = ""
        self.server_socket   = None
        self.max_connections = 15

        #thread variables
        self.thread_list = []

        #filesystem variables
        self.ftp_root   = "./ftpserver/ftproot"
        self.log_dir    = "./ftpserver/log"
        self.users_cfg  = "./ftpserver/conf/users.cfg"
        self.server_cfg = "./ftpserver/conf/fsys.cfg"
    def start(self):
        """
        goal: define server startup
        type: (self) -> ()
        """

        self.server_socket = self.setup()
        if self.server_socket:
            print("server: setup successful")
            self.eventloop()
    def eventloop(self):
        """
        goal: define server event loop
        type: (self) -> ()
        """

        try:
            while True:
                #accept connection
                user_socket, user_address = self.server_socket.accept()
                arguments = (user_socket, self.users_cfg, self.ftp_root)
                user_thread = threading.Thread(target=user_manager, args=arguments)

                #start user thread
                user_thread.start()
                self.thread_list.append(user_thread)
                print("server: connection accepted. address = {}".format(user_address))

                #cleanup thread list
                self.thread_list = [e for e in self.thread_list if e.is_alive()]
        except KeyboardInterrupt:
            print("server: keyboard interrupt. exiting...")
            self.join_threads()
        except Exception as e:
            print("server: error occured: {}".format(e))
            self.join_threads()
    def setup(self):
        """
        goal: setup server for accepting connections
        type: (self) -> socket | none
        """

        try:
            server_socket = socket(AF_INET, SOCK_STREAM)
            server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            server_socket.bind((self.server_name, int(self.server_port)))
            server_socket.listen(self.max_connections)
            return server_socket
        except Exception as e:
            print("server: socket could not be created: {}".format(e))
            return None
    def configure(self):
        """
        goal: configure server
        type: (self) -> ()
        """

        try:
            for line in open(self.server_cfg):
                #parse line
                tokens  = parser(line)
                command = tokens[0]
                arglist = tokens[1:]

                #configuration tree
                if command.startswith("#"):
                    pass
                elif command == "host":
                    self.server_name = "".join(arglist)
                elif command == "port":
                    self.server_port = "".join(arglist)
                elif command == "root_path":
                    self.ftp_root = "".join(arglist)
                elif command == "user_data_file":
                    self.users_cfg = "".join(arglist)
                elif command == "mode":
                    print("mode = {}".format("".join(arglist)))
                elif command == "data_range":
                    print("range = {}".format("".join(arglist)))
                elif command == "max_connections":
                    self.max_connections = "".join(arglist)
                elif command == "log_file":
                    print("log file = {}".format("".join(arglist)))
        except Exception as e:
            print("server: configuration error: {}".format(e))
    def arguments(self):
        """
        goal: manage command line arguments
        type: (self) -> ()
        """

        #setup parser
        parser = argparse.ArgumentParser()
        parser.add_argument("-p", "--port",   help="enter port")
        parser.add_argument("-c", "--config", help="enter path of config file")
        parser.add_argument("-m", "--max",    help="enter max num of connections")
        parser.add_argument("-d", "--dpr",    help="enter dataport range, i.e 5000-5100")
        parser.add_argument("-u", "--userdb", help="enter path of user file")

        #parse arguments
        args = parser.parse_args()

        #argument tree
        if args.port:
            self.server_port = args.port
        if args.config:
            self.server_cfg  = args.config
        if args.max:
            self.max_connections = args.max
        if args.dpr:
            print("dpr = {}".format(args.dpr))
        if args.userdb:
            self.users_cfg = args.userdb
    def join_threads(self):
        """
        goal: join all threads
        type: (self) -> ()
        """

        for thread in self.thread_list:
            thread.join()
class User:
    def __init__(self, user_socket, users_cfg, ftp_root):
        """
        goal: define class properties
        type: (self, socket, string, string) -> ()
        """

        #socket variables
        self.user_socket = user_socket

        #login variables
        self.username = ""
        self.password = ""
        self.type     = ""

        #filesystem variables
        self.user_home = ""
        self.work_dir  = ""
        self.users_cfg = os.path.abspath(users_cfg)
        self.ftp_root  = os.path.abspath(ftp_root)

        #message variables
        self.client_message = ""
        self.tokens         = []

        #dataport variables
        self.data_socket  = None
        self.data_address = ""
        self.data_port    = 0
    def start(self):
        """
        goal: define user startup
        type: (self) -> ()
        """

        if self.authenticate():
            print("user({}): credientials accepted".format(self.username))
            self.setup()
            self.eventloop()
    def eventloop(self):
        """
        goal: define user event loop
        type: (self) -> ()
        """

        while self.user_socket:
            self.client_message = get_message(self.user_socket)
            self.tokens = parser(self.client_message)
            self.dispatch()
        print("user({}): connection closed".format(self.username))
    def setup(self):
        """
        goal: set up environment for user types
        type: (self) -> ()
        """

        #type: user
        if self.type == "user":
            self.user_home = self.ftp_root + "/{}".format(self.username)
            self.work_dir  = self.user_home
            if not os.path.exists(self.user_home):
                os.mkdir(self.user_home)

        #type: admin
        if self.type == "admin":
            self.user_home = self.ftp_root
            self.work_dir  = self.user_home
    def dispatch(self):
        """
        goal: execute valid commands
        type: (self) -> ()
        """

        try:
            #parse tokens
            command = self.tokens[0].lower()
            arglist = self.tokens[1:]

            #ftp commands
            if   command == "pwd":
                if not arglist:
                    send_message(self.user_socket, "200 Command okay.")
                    ftp_pwd(self.user_socket, self.work_dir)
                else:
                    send_message(self.user_socket, "501 Syntax error in parameters or arguments.")
            elif command == "noop":
                if not arglist:
                    send_message(self.user_socket, "200 Command okay.")
                    ftp_noop(self.user_socket)
                else:
                    send_message(self.user_socket, "501 Syntax error in parameters or arguments.")
            elif command == "logout":
                if not arglist:
                    send_message(self.user_socket, "200 Command okay.")
                    ftp_logout(self.user_socket)
                    self.user_socket = None
                else:
                    send_message(self.user_socket, "501 Syntax error in parameters or arguments.")
            elif command == "type":
                if not arglist:
                    send_message(self.user_socket, "200 Command okay.")
                    ftp_type(self.user_socket)
                else:
                    send_message(self.user_socket, "501 Syntax error in parameters or arguments.")
            elif command == "port":
                if len(arglist) == 2:
                    send_message(self.user_socket, "200 Command okay.")
                    self.data_address = arglist[0]
                    self.data_port    = arglist[1]
                else:
                    send_message(self.user_socket, "501 Syntax error in parameters or arguments.")
            elif command == "list":
                if not arglist:
                    #connect to data socket
                    send_message(self.user_socket, "200 Command okay.")
                    self.data_socket = ftp_open(self.data_address, self.data_port)
                    
                    #list directory
                    ftp_list(self.data_socket, self.work_dir)
                    self.data_socket = None
                else:
                    send_message(self.user_socket, "501 Syntax error in parameters or arguments.")
            elif command == "cwd":
                if len(arglist) == 1:
                    #get newpath
                    send_message(self.user_socket, "200 Command okay.")
                    path = arglist[0]
                    new_path = ftp_cwd(self.work_dir, path)

                    #validate new path
                    if new_path:
                        self.set_workpath(new_path)
                else:
                    send_message(self.user_socket, "501 Syntax error in parameters or arguments.")
            elif command == "cdup":
                if not arglist:
                    #get newpath
                    send_message(self.user_socket, "200 Command okay.")
                    new_path = ftp_cwd(self.work_dir, "..")

                    #validate new path
                    if new_path:
                        self.set_workpath(new_path)
                else:
                    send_message(self.user_socket, "501 Syntax error in parameters or arguments.")  
            elif command == "mkd":
                if len(arglist) == 1:
                    send_message(self.user_socket, "200 Command okay.")
                    path = arglist[0]
                    ftp_mkd(self.work_dir, path)
                else:
                    send_message(self.user_socket, "501 Syntax error in parameters or arguments.")  
            elif command == "dele":
                if len(arglist) == 1:
                    send_message(self.user_socket, "200 Command okay.")
                    path = arglist[0]
                    ftp_dele(self.work_dir, path)
                else:
                    send_message(self.user_socket, "501 Syntax error in parameters or arguments.")  
            elif command == "rmd":
                if len(arglist) == 1:
                    send_message(self.user_socket, "200 Command okay.")
                    path = arglist[0]
                    ftp_rmd(self.work_dir, path, self.user_home)
                else:
                    send_message(self.user_socket, "501 Syntax error in parameters or arguments.")  
            elif command == "rn":
                if len(arglist) == 2:
                    send_message(self.user_socket, "200 Command okay.")
                    path     = arglist[0]
                    new_path = arglist[1]
                    ftp_rn(self.work_dir, path, new_path)
                else:
                    send_message(self.user_socket, "501 Syntax error in parameters or arguments.")
            elif command == "retr":
                if len(arglist) == 1:
                    #check if path exists
                    path = arglist[0]
                    does_exist = file_exists(self.work_dir, path)

                    #validate
                    if does_exist:
                        #connect to data socket
                        send_message(self.user_socket, "200 Command okay.")
                        self.data_socket = ftp_open(self.data_address, self.data_port)

                        #send file contents
                        ftp_retr(self.data_socket, self.work_dir, path)
                        self.data_socket = None
                    else:
                        send_message(self.user_socket, "450 Requested file action not taken.")
                else:
                    send_message(self.user_socket, "501 Syntax error in parameters or arguments.")
            elif command == "stor":
                if len(arglist) == 1:
                    #get filename
                    file_name = arglist[0]

                    #connect to data socket
                    send_message(self.user_socket, "200 Command okay.")
                    self.data_socket = ftp_open(self.data_address, self.data_port)

                    #send file contents
                    ftp_stor(self.data_socket, self.work_dir, file_name)
                    self.data_socket = None
                else:
                    send_message(self.user_socket, "501 Syntax error in parameters or arguments.")
            elif command == "appe":
                if len(arglist) == 1:
                    #get filename
                    file_name = arglist[0]

                    #connect to data socket
                    send_message(self.user_socket, "200 Command okay.")
                    self.data_socket = ftp_open(self.data_address, self.data_port)

                    #send file contents
                    ftp_appe(self.data_socket, self.work_dir, file_name)
                    self.data_socket = None
                else:
                    send_message(self.user_socket, "501 Syntax error in parameters or arguments.")

            #invalid command
            else:
                send_message(self.user_socket, "500 Syntax error, command unrecognized.")
        except Exception as e:
            send_message(self.user_socket, "421 Service not available, closing control connection.")
            print("user({}): error occured: {}".format(self.username, e))
            self.user_socket.close()
            self.user_socket = None
    def authenticate(self):
        """
        goal: initiate authentication with client
        type: (self) -> bool
        help: User.authenticate <-> Client.login
        """

        try: 
            #initiate login
            send_message(self.user_socket, "530 not logged in")

            #get credentials
            self.username = get_message(self.user_socket)
            self.password = get_message(self.user_socket)
            
            #validate credientials
            is_valid = self.validate()

            #reply to client
            if is_valid:
                send_message(self.user_socket, "230 user logged in, proceed")
                return True
            else:
                print("user({}): could not login".format(self.username))
                send_message(self.user_socket, "530 user not logged in")
                return False
        except Exception as e:
            print("user({}): error occured: {}".format(self.username, e))
            send_message(self.user_socket, "530 user not logged in")
            return False
    def validate(self):
        """
        goal: validate username and password
        type: (self) -> bool
        """

        #validate credentials
        try:
            for line in open(self.users_cfg):
                #check if proper parse
                tokens = parser(line)
                if len(tokens) == 3:
                    #parse tokens
                    valid_user = tokens[0]
                    valid_pass = tokens[1]
                    valid_type = tokens[2]

                    #make sure type is valid
                    if valid_type == "notallowed" or valid_type == "locked":
                        self.type = valid_type
                        return False

                    #validate variables
                    elif self.username == valid_user and self.password == valid_pass:
                        self.type = valid_type
                        return True
            return False
        except Exception as e:
            return False
    def set_workpath(self, new_path):
        """
        goal: set new work path for user
        type: (self, string) -> ()
        """

        #type: user
        if self.type == "user" and self.user_home in new_path:
            self.work_dir = new_path

        #type: admin
        elif self.type == "admin" and self.ftp_root in new_path:
            self.work_dir = new_path

#support functions
def parser(userinput):
    """
    goal: convert userinput into tokens
    type: (string) -> [string]
    """

    return userinput.strip().split()
def file_exists(work_dir, path):
    """
    goal: check if file exists
    type: (string, string) -> bool
    """

    #save previosu directory
    prev_dir = os.getcwd()

    #check if file exists
    try:
        os.chdir(work_dir)
        if os.path.exists(path) and os.path.isfile(path):
            return True
        else:
            return False
        os.chdir(prev_dir)
    except Exception as e:
        os.chdir(prev_dir)
        return False    

#message functions
def send_message(ftp_socket, message):
    """
    goal: send a message
    type: (socket, string) -> ()
    """

    if ftp_socket:
        message = "\0" if not message else message
        ftp_socket.send(message.encode())
def get_message(ftp_socket):
    """
    goal: receive a message
    type: (socket) -> string
    """

    if ftp_socket:
        return ftp_socket.recv(1024).decode()

#ftp commands
def ftp_pwd(ftp_socket, work_dir):
    """
    goal: send current working directory
    type: (socket, string) -> ()
    """

    if ftp_socket:
        root_index = work_dir.find("/ftproot")
        display_dir = work_dir[root_index:]
        send_message(ftp_socket, display_dir)
def ftp_noop(ftp_socket):
    """
    goal: simply send an ok reply
    type: (socket) -> ()
    """

    if ftp_socket:
        send_message(ftp_socket, "200 Command okay.")
def ftp_logout(ftp_socket):
    """
    goal: logout user
    type: (socket) -> ()
    """

    if ftp_socket:
        ftp_socket.close()
def ftp_type(ftp_socket):
    """
    goal: send representation type
    type: (socket) -> ()
    """

    if ftp_socket:
        send_message(ftp_socket, "ASCII")
def ftp_list(data_socket, path):
    """
    goal: list directory contents
    type: (socket, string) -> ()
    """

    if data_socket:
        try:
            contents = os.listdir(path)
            display  = "\n".join(contents)
            send_message(data_socket, display)
        except Exception as e:
            send_message(data_socket, "Cannot list directory with given arguments")
def ftp_cwd(work_dir, new_path):
    """
    goal: return valid newpath
    type: (string, string) -> string | none
    """

    #change to work directory
    prev_dir = os.getcwd()
    os.chdir(work_dir)

    #check if new path exists
    if os.path.exists(new_path) and os.path.isdir(new_path):
        new_path = os.path.abspath(new_path)
    else:
        new_path = None
    
    #go back to previous directory
    os.chdir(prev_dir)
    return new_path
def ftp_open(address, port):
    """
    goal: connect to client data socket
    type: (string, string) -> socket
    """
    
    try:
        data_socket = socket(AF_INET, SOCK_STREAM)
        data_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        data_socket.connect((address, int(port)))
        return data_socket
    except Exception as e:
        print("error: could not create socket")
        return None
def ftp_mkd(work_dir, path):
    """
    goal: make a directory
    type: (path, path) -> ()
    """

    #save previous directory
    prev_dir = os.getcwd()

    #create directory
    try:
        os.chdir(work_dir)
        os.mkdir(path)
        os.chdir(prev_dir)
    except Exception as e:
        os.chdir(prev_dir)
def ftp_dele(work_dir, path):
    """
    goal: delete a file
    type: (string, string) -> ()
    """

    #save previous directory
    prev_dir = os.getcwd()

    #remove file
    try:
        os.chdir(work_dir)
        if os.path.exists(path) and os.path.isfile(path):
            os.remove(path)
        os.chdir(prev_dir)
    except Exception as e:
        os.chdir(prev_dir)
def ftp_rmd(work_dir, path, user_home):
    """
    goal: remove directory
    type: (string, string, string) -> ()
    """

    #save previous directory
    prev_dir = os.getcwd()

    #remove directory
    try:
        os.chdir(work_dir)
        if os.path.exists(path) and os.path.isdir(path):
            path = os.path.abspath(path)
            if user_home in path and not user_home == path:
                os.rmdir(path)
        os.chdir(prev_dir)
    except Exception as e:
        os.chdir(prev_dir)
def ftp_rn(work_dir, path, new_path):
    """
    goal: rename a file
    type: (string, string, string) -> ()
    """

    #save previous directory
    prev_dir = os.getcwd()

    #rename file
    try:
        os.chdir(work_dir)
        if os.path.exists(path):
            os.rename(path, new_path)
        os.chdir(prev_dir)
    except e as Exception:
        os.chdir(prev_dir)
def ftp_retr(data_socket, work_dir, path):
    """
    goal: implement retrieve for client
    type: (socket, string, string) -> ()
    """

    if data_socket:
        #save previous directory
        prev_dir = os.getcwd()
        os.chdir(work_dir)

        #send contents of file
        with open(path, "r") as file:
            packet = file.read(1024)
            while packet:
                send_message(data_socket, packet)
                packet = file.read(1024)

        #go back to previous directory
        os.chdir(prev_dir)
def ftp_stor(data_socket, work_dir, file_name):
    """
    goal: implement store for client
    type: (socket, string) -> ()
    """

    if data_socket:
        #save previous directory
        prev_dir = os.getcwd()
        os.chdir(work_dir)

        #get first packet
        packet = get_message(data_socket)
        contents = packet

        #get rest of packets
        while packet:
            packet = get_message(data_socket)
            contents += packet

        #create and write file
        with open(file_name, "w") as file:
            file.write(contents)

        #goto previous directory
        os.chdir(prev_dir)
def ftp_appe(data_socket, work_dir, file_name):
    """
    goal: implement append for client
    type: (socket, string) -> ()
    """

    if data_socket:
        #save previous directory
        prev_dir = os.getcwd()
        os.chdir(work_dir)

        #get first packet
        packet = get_message(data_socket)
        contents = packet

        #get rest of packets
        while packet:
            packet = get_message(data_socket)
            contents += packet

        #create and write file
        with open(file_name, "a") as file:
            file.write(contents)

        #goto previous directory
        os.chdir(prev_dir)

#controller functions
def user_manager(user_socket, users_cfg, ftp_root):
    """
    goal: manage user instances
    type: (socket, string, string) -> ()
    """

    user = threading.local()
    user = User(user_socket, users_cfg, ftp_root)
    user.start()
def main():
    """
    goal: define program entrance
    type: () -> int
    """

    #define variables
    argc = len(sys.argv)
    exit_success = 0

    #configure server
    server = Server()
    server.configure()
    if argc > 1:
        client.arguments()

    #start server
    server.start()
    sys.exit(exit_success)
main()