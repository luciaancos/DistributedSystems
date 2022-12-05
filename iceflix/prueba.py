#!/usr/bin/env python3
import logging
import sys
import getpass
from hashlib import sha256
import pprint
import threading
import time

import Ice

try:
    import IceFlix  # pylint:disable=import-error

except ImportError:
    import os
    Ice.loadSlice(os.path.join(os.path.dirname(__file__),"iceflix.ice"))
    import IceFlix


logging_ = logging.getLogger('CLIENT_APPLICATION')
logging_.setLevel(logging.DEBUG)

# create console handler and set level to debug
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s')

# add formatter to ch
console_handler.setFormatter(formatter)

# add ch to logger
logging_.addHandler(console_handler)


#clase que hace la funcionalidad 
class Client(Ice.Application):
    def __init__(self):
        self.main_obj = None # el main no va a cambiar
        self.user = ""
        self.password_hash = ""
        self.token = "" 

    def run(self,argv):
        # state_thread = threading.Thread(target=self.actual_state)
        # state_thread.start()
        comm = self.communicator()
        self.connect(comm)
        self.catalog_search()
        

        comm.waitForShutdown()



    def connect(self, comm):
            if(bool(input("Would you like to determine the number of oportunities to introduce the proxy? Write yes or no:").lower() == "yes")):
                n = int(input("Introduzca el numero de intentos para introducir el proxy:"))
            else:
                n = 3 
            for i in range(n):
                main_proxy_string = input("Introduzca el proxy al servicio principal:")
                try:
                    
                    main_proxy = comm.stringToProxy(main_proxy_string)
                    self.main_obj = IceFlix.MainPrx.checkedCast(main_proxy)

                    if self.main_obj:
                        print("Conexión establecida correctamente")
                        break
                    else:
                        print("Proxy incorrecto. Vuelva a intentarlo, le quedan ", n-(i+1), "oportunidades.")
                        time.sleep(5)
                        return -1
                except Ice.NoEndpointException:
                    print("no se conecta, le quedan ", n-(i+1), "intentos" )

                # except (Ice.TemporaryUnavailable):
                #     logging_.error("El servicio principal no está disponible") #los errores estan bn asi o esto es de eventos de la entrega 2???
                #     print("Vuelva a intentarlo, le quedan ", n-(i+1), " oportunidades.")
                #tengo que poner mas excepciones de si no lo encuentra??

    def log_in(self):

        if self.user != "":
            print("There is a user already loggin, please try to log out if you want to change.")
            return -1

        if self.main_obj is None:
            print("First yo have to connect")
            return -1
            
        self.user = input("Introduzca el nombre de usuario:")
        password = getpass.getpass(prompt='Introduzca su contraseña:')
        self.password_hash = sha256(password.encode()).hexdigest()
        try:
            authenticator = self.main_obj.getAuthenticator()
            if(authenticator == None):
                raise IceFlix.TemporaryUnavailable
            
        except(Ice.ObjectNotExistException,IceFlix.TemporaryUnavailable):
            logging_.error("Sorry, the autentificacion service is temporary unavailable")
            return -1
        
        
        try:
            self.token = authenticator.refreshAuthorization(self.user, self.password_hash)
            self.user = authenticator.whois(self.token)
        except IceFlix.Unauthorized:
            logging_.error("Invalid user/password")
        else:   
            print("Successfully loged in. Enjoy!")
        return 0
    
    def actual_state(self):
        """Prints if the client is connected and if the log in is done"""
        while True:
            time.sleep(5)
            if self.main_obj == None:
                print("\nConnexion: disconnected")
            else:
                print("\nConnexion:connected")

            if self.token == "":
                print("Loged user: there is not any user loged")
            else:
                print("Loged user:", self.user)
    
    def log_out(self):
        if self.token == "":
            print("You have not loged in yet")
        else:
            self.user = ""
            self.password_hash = ""
            self.token = ""
            print("Successful log out. See you soon!")

    def admin_login(self):
        try:
            authenticator = self.main_obj.getAuthenticator()
            # if(authenticator == None):
            #     raise IceFlix.TemporaryUnavailable
            
        except(Ice.ObjectNotExistException,IceFlix.TemporaryUnavailable):
            logging_.error("Sorry, the autentificacion service is temporary unavailable")
            return -1
        else:
            admin_token = getpass.getpass(prompt='Please write your admin token:')
            isAdmin = authenticator.isAdmin(admin_token)
            print(isAdmin)
            if(isAdmin):
                self.token = admin_token
                logging_.info("Successfully loged in. Enjoy!")
            else:
                logging_.error("You are not an admin")

    def catalog_search(self):

        if self.main_obj is None:
            print("First yo have to connect")
            return -1

        #CADA VEZ QUE BUSQUEMOS ALGO RESETEAR LISTAS
        try:
            catalog = self.main_obj.getCatalog()
        except(Ice.ObjectNotExistException,IceFlix.TemporaryUnavailable):
            logging.error("Sorry, the catalog service is temporary unavailable")
        else:
        
            nameorTag = input("\Would you like to search by name or by tags? Please write name or tag:").lower()

            try:
                #por nombre
                if nameorTag == "name":
                    exact = bool(input("Would you like to make an exact search? Please write yes or no:").lower()=="yes") #si no es ni si no no volver a preguntar?????????
                    name = input("\nEscriba el titulo que quiera buscar:")

                    self.history = catalog.getTilesByName(name, exact)
                    self.view_last_search(catalog)


                #por tags
                elif nameorTag == "tag":
                    if self.user == "":
                        print("First yo have to log in")
                    else:
                        tags = input("\nIntroduzca los tags que desea buscar, escribalos separados por espacios:").split()
                        includeAllTags = bool(input("\nWould yo like to obtain media that include all the tags? Write yes or no:").lower() == "yes")
                        try:
                            self.history = catalog.getTilesByTags(tags, includeAllTags, self.token)
                            self.view_last_search(catalog)
                        except IceFlix.Unauthorized:
                            logging.error("Acceso no autorizado")
                        except(Ice.ObjectNotExistException,IceFlix.TemporaryUnavailable):
                            logging.error("Sorry, the catalog service is temporary unavailable")
                else:
                    print("La opcion introducida no es correcta") #deberia volver a dar opcion de introducirla???????????????????????
        
            except IceFlix.WrongMediaId as e:
                    logging.error("provided media ID is not found", str(e))
    


if __name__ == "__main__":
    #exit_code = client.main(sys.argv)
    sys.exit(Client().main(sys.argv))
    