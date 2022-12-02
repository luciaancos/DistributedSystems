import logging
import sys
import getpass
from hashlib import sha256

import Ice

try:
    import IceFlix  # pylint:disable=import-error

except ImportError:
    import os
    Ice.loadSlice(os.path.join(os.path.dirname(__file__),"iceflix.ice"))
    import IceFlix



LOG_FORMAT = '%(asctime)s - %(levelname)-7s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'


class Client(Ice.Application):
    def __init__(self):
        self.main = None # el main no va a cambiar
        self.user = ""
        self.password_hash = ""
        self.token = ""
        #un self autenticator por que lo uso varias veces???? este puede que si cambie 

    def run(self, argv):
        while True:
            self.actual_state()#metodo que imprima si hay conexion y si la sesion esta iniciada
            self.connect()
        #autentication no lo llamamos siempre, lo que se haga de forma anonima es sin login??????
        #como se cuando revoca un token???????????
        #imprimir todo el rato el estado de la conexion????

    def actual_state(self):
        """Prints if the client is connected and if the log in is done"""
        if self.main == None:
            print("\nConnexion: disconnected")
        else:
            print("\nConnexion:connected")

        if self.token == "":
            print("\nLoged user: there is not any user loged")
        else:
            try:
                authenticator = self.main
                user_name = authenticator.whois(self.token)
                print("Loged user: ", user_name)
            except (IceFlix.TemporaryUnavailable, AttributeError):
                print("El servicio de autentificacion no está disponible")

    def connect(self):
        """Comprueba el proxy intruducido por linea de comandos, en caso de ser correcto establece la conexion"""
        main_proxy_string = input('Bienvenido a IceFlix, Introduzca el proxy al servicio principal:')
        #definir numero de veces que puede introducir el proxy??? habria que cambiar el 2-i
        
        for i in range(3):
            try:
                comm = self.communicator()
                main_proxy = comm.stringToProxy(main_proxy_string)
                self.main = IceFlix.MainPrx.checkedCast(main_proxy)

                if self.main:
                    print("Conexión establecida correctamente")
                else:
                    print("Proxy incorrecto. Vuelva a intentarlo, le quedan ", 2-i, " oportunidades.")

            except (Ice.TemporaryUnavailable):
                logging.error("El servicio principal no está disponible") #los errores estan bn asi o esto es de eventos de la entrega 2???
                print("Vuelva a intentarlo, le quedan ", 2-i, " oportunidades.")
            #tengo que poner mas excepciones de si no lo encuentra??

    def log_in(self):

        if self.current_user is not None:
            print('\nYa hay un usuario registrado')
            
        self.user = input("Introduzca el nombre de usuario: \n> ")
        password = getpass.getpass(prompt='\nIntroduzca su contraseña:')
        self.password_hash = sha256(password.encode()).hexdigest()
        try:
            authenticator = self.main.getAuthenticator()
            
        except IceFlix.TemporaryUnavailable:
            logging.error("El servicio de autentificacion no está disponible")
        
        if authenticator.ice_isA('::iceflix::Authenticator'):
            try:
                self.token = authenticator.refreshAuthorization(self.user, self.pass_hash)
                self.user = authenticator.whois(self.token)
                self.password_hash = self.password_hash #como pongo aqui la contraseñ apara quela compruebe????
            except IceFlix.Unauthorized:
                logging.error('Usuario o contraseña incorrectos')

        print("Usuario registrado correctamente")


    def log_out(self):
        if self.token is None:
            print('\n aun no te has registrado')
        else:
            self.user = None
            self.password_hash = None
            self.token = None
            print('\nSe ha cerrado la sesion')
    
    def catalog_search(self):
        catalog = self.main.getCatalog()
        history = []
        
        if catalog.ice_isA('::IceFlix::MediaCatalog')==False:
            print('El proxy no es de tipo catalog')
        
        nameorTag = input("\Quiere hacer la busqueda por nombre o por tags, escriba nombre o tag:").lower()

        try:
            #por nombre
            if nameorTag == "nombre":
                exact = bool(input("\nQuiere realizar una busqueda exacta? Escriba si o no:")=="si").lower() #si no es ni si no no volver a preguntar?????????
                name = input("\nEscriba el titulo que quiera buscar:")

                history.append(catalog.getTilesByName(name, exact))

            #por tags
            elif nameorTag == "tag":
                tags = input("\nIntroduzca los tags que desea buscar, escribalos separados por espacios:").split()
                includeAllTags = bool(input("\nWould yo like to obtain media that include all the tags? Write yes or no:") == "yes").lower()
                try:
                    history.append(catalog.getTilesByTags(tags, includeAllTags, self.token))
                except IceFlix.Unauthorized:
                    logging.error("Acceso no autorizado")
            else:
                print("La opcion introducida no es correcta") #deberia volver a dar opcion de introducirla???????????????????????
       
        except IceFlix.WrongMediaId as e:
                logging.error("provided media ID is not found", str(e))

            
    def add_user(self):
        user = input("\nIntroduzca el nombre de usuario")
        password = input("\nIntroduzca contraseña")
        password_hash = sha256(password.encode()).hexdigest()
        admin_token = input("\nIntroduzca el admin token")
        try:
            authenticator = self.main.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            logging.error('El servicio de autentificacion no está disponible')
        
        if authenticator.ice_isA('::IceFlix::Authenticator') == False:
            print("EL proxy no es de tipo Authenticator")
        
        try:
            authenticator.addUser(user, password_hash, admin_token)
            print("The user has been added")
        except IceFlix.Unauthorized:
                logging.error('Provided authentication token is wrong')

    
    def delete_user(self):
        user = input("\nIntroduzca el nombre de usuario que quiere eliminar")
        admin_token = input("\nIntroduzca el admin token ")
        try:
            authenticator = self.main.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            logging.error('El servicio de autentificacion no está disponible')
        
        if authenticator.ice_isA('::IceFlix::Authenticator') == False:
            print("EL proxy no es de tipo Authenticator")

        try:
            authenticator.removeUser(user, admin_token)
            print("The user has been removed")
        except IceFlix.Unauthorized:
            logging.error('Provided authentication token is wrong')
