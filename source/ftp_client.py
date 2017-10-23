# imports
import argparse
import os
import sys
from socket import *


# classes
class Client:
    def __init__(self):
        """
        goal: define class properties
        type: (self) -> ()
        """

        # input variables
        self.userinput = ""
        self.tokens    = []

        # socket variables
        self.ftp_socket = None
        self.host       = ""
        self.port       = "21"

        # login variables
        self.username = ""
        self.password = ""

        # filesystem variables
        self.client_cfg = "./ftp_client.cfg"
        self.test_file  = "./tests/testfile.txt"

        # dataport variables
        self.data_socket      = None
        self.data_address     = ""
        self.dataport_min     = 60020
        self.dataport_max     = 61000
        self.data_port        = self.dataport_min
        self.next_dataport    = 1
        self.dataport_backlog = 1
    def start(self):
        """
        goal: define client startup
        type: (self) -> ()
        """

        self.eventloop()
    def eventloop(self):
        """
        goal: define client eventloop
        type: (self) -> ()
        """

        while True:
            self.userinput = menu("ftp>")
            self.tokens    = parser(self.userinput)
            self.dispatch()
    def configure(self):
        """
        goal: configure client
        type: (self) -> ()
        """

        try: 
            for line in open(self.client_cfg):
                tokens  = parser(line)
                command = tokens[0]
                arglist = tokens[1:]

                if command.startswith("# "):
                    pass
                elif command == "host":
                    self.host = "".join(arglist)
                elif command == "port":
                    self.port = "".join(arglist)
                elif command == "data_port_max":
                    self.dataport_max = "".join(arglist)
                elif command == "data_port_min":
                    self.dataport_min = "".join(arglist)
                elif command == "default_ftp_port":
                    self.port = "".join(arglist)
                elif command == "default_mode":
                    print("default mode = {}".format("".join(arglist)))
                elif command == "default_debug_mode":
                    print("default debug mode = {}".format("".join(arglist)))
                elif command == "default_verbose_mode":
                    print("default verbose mode = {}".format("".join(arglist)))
                elif command == "default_test_file":
                    self.test_file = "".join(arglist)
                elif command == "default_log_file":
                    print("default log file = {}".format("".join(arglist)))
        except Exception as e:
            print("ftp: configuration error: {}".format(e))
    def arguments(self):
        """
        goal: manage command line arguments
        type: (self) -> ()
        """

        arg_parser = argparse.ArgumentParser()
        arg_parser.add_argument("-H", "--hostname", help="enter hostname")
        arg_parser.add_argument("-u", "--username", help="enter username")
        arg_parser.add_argument("-w", "--password", help="enter password")
        arg_parser.add_argument("-fp", "--ftp_port", help="enter port")
        arg_parser.add_argument("-d", "--dataport", help="enter dataport range")
        arg_parser.add_argument("-c", "--config",   help="enter configuration file")
        arg_parser.add_argument("-t", "--test",     help="enter test file")
        arg_parser.add_argument("-L", "--log",      help="enter log file")
        arg_parser.add_argument("-D", "--debug",    help="toogle debug  mode", choices=["on", "off"])
        arg_parser.add_argument("-P", "--passive",  help="passive mode", action="store_true")
        arg_parser.add_argument("-A", "--active",   help="active mode",  action="store_true")
        arg_parser.add_argument("-V", "--verbose",  help="verbose mode", action="store_true")
        arg_parser.add_argument("-T", "--test_default", help="run default test", action="store_true")
        arg_parser.add_argument("--all",     help="all output to log file, still display", action="store_true")
        arg_parser.add_argument("--lall",    help="log all output to this file")
        arg_parser.add_argument("--only",    help="only log all output", action="store_true")
        arg_parser.add_argument("--version", help="display version",     action="store_true")
        arg_parser.add_argument("--info",    help="display client info", action="store_true")
        args = arg_parser.parse_args()

        if args.hostname:
            self.host = args.hostname
        if args.username:
            self.username = args.username
        if args.password:
            self.password = args.password
        if args.ftp_port:
            self.port = args.ftp_port
        if args.dataport:
            self.data_port = args.dataport
        if args.config:
            self.client_cfg = args.config
        if args.test:
            print("test = {}".format(args.test))
        if args.log:
            print("log = {}".format(args.log))
        if args.debug:
            print("debug = {}".format(args.debug))
        if args.passive:
            print("passive = {}".format(args.passive))
        if args.active:
            print("active = {}".format(args.active))
        if args.verbose:
            print("verbose = {}".format(args.verbose))
        if args.test_default:
            self.test_me()
            sys.exit()
        if args.all:
            print("all = {}".format(args.all))
        if args.lall:
            print("lall = {}".format(args.lall))
        if args.only:
            print("only = {}".format(args.only))
        if args.version:
            print("version: 0.1")
            sys.exit()
        if args.info:
            print("name: Andrew Cristancho")
            print("id:   2702278")
            sys.exit()
    def dispatch(self):
        """
        goal: execute valid commands
        type: (self) -> ()
        """

        try:
            command = self.tokens[0].lower()
            arglist = self.tokens[1:]

            if   command in ("exit", "bye", "quit"):
                if self.ftp_socket:
                    ftp_logout(self.ftp_socket)
                    self.logout()
                sys.exit()
            elif command in ("pwd",):
                if not arglist:
                    ftp_pwd(self.ftp_socket)
            elif command in ("noop",):
                if not arglist:
                    ftp_noop(self.ftp_socket)
            elif command in ("logout", "close"):
                if not arglist:
                    print("Logged out", self.username)
                    ftp_logout(self.ftp_socket)
                    self.logout()
            elif command in ("type",):
                if not arglist:
                    ftp_type(self.ftp_socket)
            elif command in ("list", "dir", "ls"):
                if not arglist:
                    self.data_socket = self.dataport()
                    if self.data_socket:
                        ftp_port(self.ftp_socket, self.data_address, self.data_port)
                        ftp_list(self.ftp_socket, self.data_socket)
                        self.data_socket = None
            elif command in ("cwd", "cd"):
                if len(arglist) == 1:
                    path = arglist[0]
                    ftp_cwd(self.ftp_socket, path)
            elif command in ("cdup",):
                if not arglist:
                    ftp_cdup(self.ftp_socket)
            elif command in ("mkd", "mkdir"):
                if len(arglist) == 1:
                    path = arglist[0]
                    ftp_mkd(self.ftp_socket, path)
            elif command in ("dele", "delete"):
                if len(arglist) == 1:
                    path = arglist[0]
                    ftp_dele(self.ftp_socket, path)
            elif command in ("rmd", "rmdir"):
                if len(arglist) == 1:
                    path = arglist[0]
                    ftp_rmd(self.ftp_socket, path)
            elif command in ("rn", "rename"):
                if len(arglist) == 2:
                    path     = arglist[0]
                    new_path = arglist[1]
                    ftp_rn(self.ftp_socket, path, new_path)
            elif command in ("retr", "get"):
                if len(arglist) == 1:
                    # create data socket
                    path = arglist[0]
                    self.data_socket = self.dataport()

                    # retrieve file
                    if self.data_socket:
                        ftp_port(self.ftp_socket, self.data_address, self.data_port)
                        ftp_retr(self.ftp_socket, self.data_socket, path)
                        self.data_socket = None
            elif command in ("stor", "put", "send"):
                if len(arglist) == 1:
                    # create data socket
                    path = arglist[0]
                    self.data_socket = self.dataport()

                    # send file
                    if self.data_socket and os.path.exists(path) and os.path.isfile(path):
                        ftp_port(self.ftp_socket, self.data_address, self.data_port)
                        ftp_stor(self.ftp_socket, self.data_socket, path)
                        self.data_socket = None
            elif command in ("appe", "append"):
                if len(arglist) == 1:
                    # create data socket
                    path = arglist[0]
                    self.data_socket = self.dataport()

                    # send file
                    if self.data_socket and os.path.exists(path) and os.path.isfile(path):
                        ftp_port(self.ftp_socket, self.data_address, self.data_port)
                        ftp_appe(self.ftp_socket, self.data_socket, path)
                        self.data_socket = None
            elif command in ("open", "ftp"):
                if len(arglist) == 2 and arglist[1].isnumeric():
                    # attempt connection
                    host = arglist[0]
                    port = arglist[1]
                    self.ftp_socket = ftp_open(host, int(port))

                    # login to server
                    if self.ftp_socket:
                        # get server reply
                        print("Connected to {}".format(host))
                        reply = get_message(self.ftp_socket)
                        code, message = parse_reply(reply)

                        # login tree
                        if code != "230":
                            self.login()
                        else:
                            print("User logged in, proceed")
            
            # debugging
            elif command == "try":
                # fast way to try (host, address) from config, for debugging
                if len(arglist) == 0:
                    # atttempt connection
                    self.ftp_socket = ftp_open(self.host, int(self.port))
                    reply = get_message(self.ftp_socket)
                    code, message = parse_reply(reply)

                    # not logged in
                    if code == "530":
                        self.login()
                    else:
                        print("already logged in")

            else:
                print("Invalid command")
        except Exception as e:
            print("Error:", e)
    def login(self):
        """
        goal: define login protocol
        type: (self) -> ()
        help: Client.login <-> User.authenticate 
        """

        self.username = menu("username:")
        self.password = menu("password:")

        send_message(self.ftp_socket, self.username)
        send_message(self.ftp_socket, self.password)

        reply = get_message(self.ftp_socket)
        code, message = parse_reply(reply)

        if code == "230":
            print("Logged into {}".format(self.host))
        else:
            print("Failed to log into {}".format(self.host))
            self.logout()
    def logout(self):
        """
        goal: define logout protocol
        type: (self) -> ()
        """

        self.username = ""
        self.password = ""
        self.ftp_socket.close()
        self.ftp_socket = None
    def dataport(self):
        """
        goal: create dataport
        type: (self) -> socket | none
        """

        try:
            self.data_address = gethostbyname("")
            self.next_dataport += 1
            self.data_port = (self.dataport_min + self.next_dataport) % self.dataport_max

            # create dataport
            data_socket = socket(AF_INET, SOCK_STREAM)
            data_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            data_socket.bind((self.data_address, self.data_port))
            data_socket.listen(self.dataport_backlog)
            return data_socket
        except Exception as e:
            print("Dataport error:", e)
            return None
    def test_me(self):
        """
        goal: run test file
        type: (self) -> ()
        """

        if os.path.exists(self.test_file) and os.path.isfile(self.test_file):
            for line in open(self.test_file):
                tokens  = parser(line)
                command = tokens[0]

                if command.startswith("# ") or not command:
                    pass
                else:
                    self.tokens = tokens
                    self.dispatch()
                    pause = input("(press enter to continue): ")


# interface functions
def menu(prompt):
    """
    goal: get and return userinput
    type: (string) -> string
    """

    userinput = input("{} ".format(prompt))
    return userinput.strip()
def parser(userinput):
    """
    goal: convert userinput into tokens
    type: (string) -> [string]
    """

    return userinput.strip().split()


# message functions
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
def parse_reply(reply):
    """
    goal: parse ftp server replay 
    type: (string) -> (string, string)
    """

    tokens  = parser(reply)
    code    = tokens[0]
    message = " ".join(tokens[1:])
    return code, message


# ftp commands
def ftp_pwd(ftp_socket):
    """
    goal: print working directory
    type: (socket) -> ()
    """
    
    if ftp_socket:
        send_message(ftp_socket, "pwd")
        reply = get_message(ftp_socket)
        code, message = parse_reply(reply)

        if code == "200":
            message = get_message(ftp_socket)
            print(message)
def ftp_noop(ftp_socket):
    """
    goal: simply recieve an ok reply
    type: (socket) -> ()
    """

    if ftp_socket:
        send_message(ftp_socket, "noop")
        reply = get_message(ftp_socket)
        code, message = parse_reply(reply)

        if code == "200":
            reply = get_message(ftp_socket)
            code, message = parse_reply(reply)
            print(message)
def ftp_logout(ftp_socket):
    """
    goal: logout user
    type: (socket) -> ()
    """

    if ftp_socket:
        send_message(ftp_socket, "logout")
        reply = get_message(ftp_socket)
def ftp_type(ftp_socket):
    """
    goal: print out representation type
    type: (socket) -> ()
    """

    if ftp_socket:
        send_message(ftp_socket, "type")
        reply = get_message(ftp_socket)
        code, message = parse_reply(reply)

        if code == "200":
            rep_type = get_message(ftp_socket)
            print("type =", rep_type)
def ftp_port(ftp_socket, address, port):
    """
    goal: let server know about data port
    type: (socket, string, int) -> ()
    """

    if ftp_socket:
        port_command = "port {} {}".format(address, port)
        send_message(ftp_socket, port_command)
        reply = get_message(ftp_socket)
def ftp_list(ftp_socket, data_socket):
    """
    goal: list directory contents
    type: (socket, socket) -> ()
    """

    if ftp_socket and data_socket:
        send_message(ftp_socket, "list")
        reply = get_message(ftp_socket)
        code, message = parse_reply(reply)

        if code == "200":
            data_connection, data_host = data_socket.accept()
            contents = get_message(data_connection)

            print(contents)
            data_connection.close()
def ftp_open(host, port=21):
    """
    goal: create socket to host
    type: (string, int) -> socket | none
    """

    try:
        ftp_socket = socket(AF_INET, SOCK_STREAM)
        ftp_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        ftp_socket.connect((host, port))
        return ftp_socket
    except Exception as e:
        print("ftp: Can't connect to '{}': {}".format(host, e))
        return None
def ftp_cwd(ftp_socket, path):
    """
    goal: change working directory
    type: (socket, path) -> ()
    """

    if ftp_socket:
        cwd_command = "{} {}".format("cwd", path)
        send_message(ftp_socket, cwd_command)
        reply = get_message(ftp_socket)
def ftp_cdup(ftp_socket):
    """
    goal: change to parent directory
    type: (socket) -> ()
    """

    if ftp_socket:
        send_message(ftp_socket, "cdup")
        reply = get_message(ftp_socket)
def ftp_mkd(ftp_socket, path):
    """
    goal: make a directory
    type: (socket, string) -> ()
    """

    if ftp_socket:
        mkd_command = "{} {}".format("mkd", path)
        send_message(ftp_socket, mkd_command)
        reply = get_message(ftp_socket)
def ftp_dele(ftp_socket, path):
    """
    goal: delete a file
    type: (socket, string) -> () 
    """

    if ftp_socket:
        dele_command = "{} {}".format("dele", path)
        send_message(ftp_socket, dele_command)
        reply = get_message(ftp_socket)
def ftp_rmd(ftp_socket, path):
    """
    goal: remove directory
    type: (socket, string) -> ()
    """

    if ftp_socket:
        rmd_command = "{} {}".format("rmd", path)
        send_message(ftp_socket, rmd_command)
        reply = get_message(ftp_socket)
def ftp_rn(ftp_socket, path, new_path):
    """
    goal: rename a file
    type: (socket, string, string) -> ()
    """

    if ftp_socket:
        rn_command = "{} {} {}".format("rn", path, new_path)
        send_message(ftp_socket, rn_command)
        reply = get_message(ftp_socket)
def ftp_retr(ftp_socket, data_socket, path):
    """
    goal: retrieve a file
    type: (socket, socket, path) -> ()
    """

    if ftp_socket and data_socket: 
        retr_command = "{} {}".format("retr", path)
        send_message(ftp_socket, retr_command)
        reply = get_message(ftp_socket)
        code, message = parse_reply(reply)

        if code == "200":
            data_connection, data_host = data_socket.accept()
            packet = get_message(data_connection)
            contents = packet
            
            while packet:
                packet = get_message(data_connection)
                contents += packet

            filename = os.path.basename(path)
            with open(filename, "w") as file:
                file.write(contents)
def ftp_stor(ftp_socket, data_socket, path):
    """
    goal: send a file
    type: (socket, socket, string) -> ()
    """

    if ftp_socket and data_socket and os.path.exists(path) and os.path.isfile(path):
        stor_command = "{} {}".format("appe", os.path.basename(path))
        send_message(ftp_socket, stor_command)
        reply = get_message(ftp_socket)
        code, message = parse_reply(reply)

        if code == "200":
            data_connection, data_host = data_socket.accept()

            with open(path, "r") as file:
                packet = file.read(1024)
                while packet:
                    send_message(data_connection, packet)
                    packet = file.read(1024)
def ftp_appe(ftp_socket, data_socket, path):
    """
    goal: append a file
    type: (socket, socket, string) -> ()
    """

    if ftp_socket and data_socket and os.path.exists(path) and os.path.isfile(path):
        appe_command = "{} {}".format("appe", os.path.basename(path))
        send_message(ftp_socket, appe_command)
        reply = get_message(ftp_socket)
        code, message = parse_reply(reply)

        if code == "200":
            data_connection, data_host = data_socket.accept()

            with open(path, "r") as file:
                packet = file.read(1024)
                while packet:
                    send_message(data_connection, packet)
                    packet = file.read(1024)


# controller functions
def main():
    """
    goal: define program entrance
    type: () -> int
    """

    argc = len(sys.argv)
    exit_success = 0

    client = Client()
    client.configure()
    if argc > 1:
        client.arguments()

    client.start()
    sys.exit(exit_success)
main()