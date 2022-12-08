#!/usr/bin/env python3
import cmd
import getpass
from hashlib import sha256
import logging
import time
from colorama import Style, Fore
import Ice

try:
    import IceFlix  # pylint:disable=import-error

except ImportError:
    import os
    Ice.loadSlice(os.path.join(os.path.dirname(__file__),"iceflix.ice"))
    import IceFlix

LOG_FORMAT = '%(asctime)s - %(levelname)-7s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'

logging_ = logging.getLogger('CLIENT_APPLICATION')
logging_.setLevel(logging.DEBUG)

# create console handler and set level to debug
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)-7s - %(module)s:%(funcName)s:%(lineno)d - %(message)s')

# add formatter to ch
console_handler.setFormatter(formatter)

# add ch to logger
logging_.addHandler(console_handler)



class Client_cmd(cmd.Cmd):


    intro = Style.BRIGHT+ Fore.LIGHTMAGENTA_EX +  'Welcome to Iceflix! 😀' + Style.NORMAL + Fore.BLACK + '\nWrite "help" or "?" to see the options:'
    
    def __init__(self, main_obj):

        #### THIS IS THE LINE YOU FORGOT!!!!
        super(Client_cmd, self).__init__()

        self.main_obj = main_obj # el main no va a cambiar
        self.user = ""
        self.password_hash = ""
        self.token = "" 
        self.history = [] #lista de strings que obtenemos en la ultima busqueda
        self.history_media = [] #lusta de objetos media que obtenemos en la ultima busqueda


    def do_connect(self, _):
        if self.main_obj is not None:
            print("You are already connected.")
        else:
            for i in range(3):
                main_proxy_string = input("Please, introduce the main proxy:")
                try:
                    comm = self.communicator()
                    main_proxy = comm.stringToProxy(main_proxy_string)
                    self.main_obj = IceFlix.MainPrx.checkedCast(main_proxy)

                    if self.main_obj:
                        print("Successfully connected")
                        return main_proxy
                    else:
                        print("Incorrect proxy. Please try again, ", 2-i, "remaining oportunities.")
                        time.sleep(5)
                        return -1
                except Ice.NoEndpointException:
                    print("Sorry, it does not connect,  ", 2-i, "remaining oportunities" )
                except (Ice.TemporaryUnavailable):
                    logging.error("Sorry, the main service is not available") 
                    print("Please try again, ", 2-i, "remaining oportunities.")

    def actual_state(self):
        """Prints if the client is connected and logged"""
        if self.main_obj == None:
            print("\nConnexion: disconnected")
        else:
            print("\nConnexion:connected")

            if self.token == "":
                print("Loged user: there is not any user loged")
            else:
                try:
                    authenticator = self.main_obj.getAuthenticator()
                    user_name = authenticator.whois(self.token)
                    print("Loged user: ", user_name)
                except (IceFlix.TemporaryUnavailable):
                    print("El servicio de autentificacion no está disponible")
    def do_login(self, _):
        if self.user != "":
            print("There is a user already loggin, please try to log out if you want to change.")

        if self.main_obj is None:
            print("First yo have to connect")
        else:
            try:
                authenticator = self.main_obj.getAuthenticator()
                
            except(Ice.ObjectNotExistException,IceFlix.TemporaryUnavailable):
                logging.error("Sorry, the autentificacion service is temporary unavailable")
            else:
                self.user = input("Introduce the user name: ")
                password = getpass.getpass(prompt='ntrodice the password: ')
                self.password_hash = sha256(password.encode()).hexdigest()
                        
                try:
                    self.token = authenticator.refreshAuthorization(self.user, self.password_hash)
                    self.user = authenticator.whois(self.token)
                except IceFlix.Unauthorized:
                    logging.error("Invalid user/password")
                else:   
                    print("Successfully loged in. Enjoy!")
                return 0