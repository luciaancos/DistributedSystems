#!/usr/bin/env python3
import logging
import sys
import getpass
from hashlib import sha256
import pprint
import time

import Ice

try:
    import IceFlix  # pylint:disable=import-error

except ImportError:
    import os
    Ice.loadSlice(os.path.join(os.path.dirname(__file__),"iceflix.ice"))
    import IceFlix




#clase que hace la funcionalidad 
class Client(Ice.Application):
    def __init__(self):
        self.main_obj = None # el main no va a cambiar
        self.user = ""
        self.password_hash = ""
        self.token = "" 

    def run(self,argv):
        self.connect()
        self.admin_login()

    def connect(self):
            if(bool(input("Would you like to determine the number of oportunities to introduce the proxy? Write yes or no:").lower() == "yes")):
                n = int(input("Introduzca el numero de intentos para introducir el proxy:"))
            else:
                n = 3 
            for i in range(n):
                main_proxy_string = input("Introduzca el proxy al servicio principal:")
                try:
                    comm = self.communicator()
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
                #     logging.error("El servicio principal no está disponible") #los errores estan bn asi o esto es de eventos de la entrega 2???
                #     print("Vuelva a intentarlo, le quedan ", n-(i+1), " oportunidades.")
                #tengo que poner mas excepciones de si no lo encuentra??

    def admin_login(self):
        admin_token = getpass.getpass(prompt='Please write your admin token:')
        try:
            authenticator = self.main_obj.getAuthenticator()
            # if(authenticator == None):
            #     raise IceFlix.TemporaryUnavailable
            
        except(Ice.ObjectNotExistException,IceFlix.TemporaryUnavailable):
            logging.error("Sorry, the autentificacion service is temporary unavailable")
            return -1
        else:
            isAdmin = authenticator.isAdmin(admin_token)
            if(isAdmin):
                logging.info("Successfully loged in. Enjoy!")
            else:
                logging.error("You are not an admin")

    


if __name__ == "__main__":
    #exit_code = client.main(sys.argv)
    sys.exit(Client().main(sys.argv))