import logging
import sys
import getpass
from hashlib import sha256
from __future__ import annotations
import pprint
import time

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
        self.main_obj = None # el main no va a cambiar
        self.user = ""
        self.password_hash = ""
        self.token = "" 
        self.history = [] #lista de strings que obtenemos en la ultima busqueda
        self.history_media = [] #lusta de objetos media que obtenemos en la ultima busqueda
        #un self autenticator por que lo uso varias veces???? este puede que si cambie 

    def run(self, argv):
        while True:
            self.actual_state()#metodo que imprima si hay conexion y si la sesion esta iniciada
            time.sleep(5)
            self.connect()
        #autentication no lo llamamos siempre, lo que se haga de forma anonima es sin login??????
        #como se cuando revoca un token???????????
        #imprimir todo el rato el estado de la conexion????

    def actual_state(self):
        """Prints if the client is connected and if the log in is done"""
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

                except (Ice.TemporaryUnavailable):
                    logging.error("El servicio principal no está disponible") #los errores estan bn asi o esto es de eventos de la entrega 2???
                    print("Vuelva a intentarlo, le quedan ", n-(i+1), " oportunidades.")
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
            logging.error("Sorry, the autentificacion service is temporary unavailable")
            return -1
        
        
        try:
            self.token = authenticator.refreshAuthorization(self.user, self.pass_hash)
            self.user = authenticator.whois(self.token)
            self.password_hash = self.password_hash #como pongo aqui la contraseñ apara quela compruebe????
        except IceFlix.Unauthorized:
            logging.error("Invalid user/password")

        print("Successfully loged in. Enjoy!")
        return 0


    def log_out(self):
        if self.token == "":
            print("You have not loged in yet")
        else:
            self.user = ""
            self.password_hash = ""
            self.token = ""
            print("Successful log out. See you soon!")
    

    def catalog_search(self):

        #CADA VEZ QUE BUSQUEMOS ALGO RESETEAR LISTAS

        catalog = self.main_obj.getCatalog()
        
        if catalog.ice_isA('::IceFlix::MediaCatalog')==False:
            print("It is not a catalog proxy")
        
        nameorTag = input("\Would you like to search by name or by tags? Please write name or tag:").lower()

        try:
            #por nombre
            if nameorTag == "name":
                exact = bool(input("Would you like to make an exact search? Please write yes or no:")=="yes").lower() #si no es ni si no no volver a preguntar?????????
                name = input("\nEscriba el titulo que quiera buscar:")

                self.history = catalog.getTilesByName(name, exact)
                self.view_last_search(catalog)


            #por tags
            elif nameorTag == "tag":
                tags = input("\nIntroduzca los tags que desea buscar, escribalos separados por espacios:").split()
                includeAllTags = bool(input("\nWould yo like to obtain media that include all the tags? Write yes or no:") == "yes").lower()
                try:
                    self.history = catalog.getTilesByTags(tags, includeAllTags, self.token)
                    self.view_last_search(catalog)
                except IceFlix.Unauthorized:
                    logging.error("Acceso no autorizado")
            else:
                print("La opcion introducida no es correcta") #deberia volver a dar opcion de introducirla???????????????????????
       
        except IceFlix.WrongMediaId as e:
                logging.error("provided media ID is not found", str(e))


    def view_last_search(self,catalog): #history es lista de strings
        if len(self.history == 0):
            logging.error("\nNo media found.")

        else:
            self.history_media = []
            for tile in self.history: #para cada componente de la lista de strings
                try:
                    media = catalog.getTile(tile, self.token) #conseguimos el objeto media
                    self.history_media.append(media) #en history media metemos objetos media
                except IceFlix.WrongMediaId:
                    logging.error("The id is incorrect")
                except IceFlix.TemporaryUnavailable:
                    logging.error("The requested item is currently unavailable")
                except IceFlix.Unauthorized:
                    logging.error("Authentication token is wrong")

            counter = 1
            for media in self.history_media:
                print(str(counter) + ': ' + media.info.name)
                counter += 1

        # if (bool(input("\nDo yo want to select a title? Write yes or no: ")).lower() == "yes"):
        #     selected = self.select_last_search() #selected es el objeto media que elegimos
            
        #     self.edit_catalog(selected,catalog)

        #si dice que no quiere seleccionar no hace nada, deberia volver a pantalla principal
        return 0

    def select_last_search(self, catalog):
        self.view_last_search(catalog)
        while True: 
                try:      
                    selected = int(input("\nSelect the number of the title, choose from 1 to ", len(self.history_media)+1, ": "))
                    if selected> len(self.history_media)+1 or selected < 0:
                        raise ValueError
                    else:
                        break

                except ValueError:
                    logging.error("Incorrect option, try again please")
                    continue
        
        return self.history_media[selected]
            


    def edit_catalog(self,selected, catalog):
        while True:
            print('¿What would yo like to do with? (' + selected.info.name + ')')
            print('1. Add tags')
            print('2. Remove tags')
            print('3. Exit')

            option = input()

            if option == '1':
                try:
                    tags = input("Introduce the tags you want to add: ").lower().split()
                    catalog.add_tags_tile(selected.mediaId, tags, self.token)
                    logging.info("Tags added correctly")
                except IceFlix.Unauthorized:
                    logging.error("Provided user token is wrong")
                except IceFlix.WrongMediaId:
                    logging.error("Media id can not be found")
                break

            elif option == '2':
                try:
                    tags = input("Introduce the tags you want to remove: ").lower().split()
                    catalog.remove_tags_tile(selected.mediaId, tags, self.token)
                    logging.info("Tags removed correctly")
                except IceFlix.Unauthorized:
                    logging.error("Provided user token is wrong")
                except IceFlix.WrongMediaId:
                    logging.error("Media id can not be found")
                break

            elif option == '3':
                break

            else:
                print("Incorrect option, please try again")


    #ADMIN!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!      

    def add_user(self):
        user = input("\nIntroduzca el nombre de usuario")
        password = input("\nIntroduzca contraseña")
        password_hash = sha256(password.encode()).hexdigest()
        admin_token = input("\nIntroduzca el admin token")
        try:
            authenticator = self.main_obj.getAuthenticator()
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
            authenticator = self.main_obj.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            logging.error('El servicio de autentificacion no está disponible')
        
        if authenticator.ice_isA('::IceFlix::Authenticator') == False:
            print("EL proxy no es de tipo Authenticator")

        try:
            authenticator.removeUser(user, admin_token)
            print("The user has been removed")
        except IceFlix.Unauthorized:
            logging.error('Provided authentication token is wrong')

    def rename_media(self):
        catalog = self.main_obj.getCatalog()
        print("Select the one you would like to change:")
        selected = self.select_last_search(catalog)
        new_name = input("Write the new name please: ")
        try:
            catalog.renameTile(selected.mediaId, new_name, self.token) #self token porque esto va con el admin y hay que pedirselo antes de entrar
            selected.info.name = new_name
            print("Name changed successfuly")
        except IceFlix.Unauthorized:
            logging.error("Provided user token is wrong")
        except IceFlix.WrongMediaId:
            logging.error("Media id can not be found")
            
    # def upload_media(self):



# class MediaUploader(IceFlix.MediaUploader):
#     '''Clase del uploader de archivos media'''

#     def __init__(self, filename):
#         self.filename = filename

#         try:
#             self.fdir = open(filename, 'rb')
#         except FileNotFoundError:
#             logging.error('¡No se encontró el archivo!')
#         except IsADirectoryError:
#             logging.error('¡Se indicó un directorio, no un archivo!')

#     def receive(self, size, current=None):
#         '''Recibe el archivo media seleccionado'''

#         chunk = self.fdir.read(size)
#         return chunk

#     def close(self, current=None):
#         '''Cierra y destruye el uploader'''

#         self.fdir.close()
#         current.adapter.remove(current.id)


# class FileUploaderServant(IceFlix.FileUploader):
#     def __init__(self):
        


# class MediaUploaderI(IceFlix.MediaUploader):
#     """Implementación de la interfaz MediaUploader del módulo IceFlix"""
#     def __init__(self, file_name):
#         """Inicialización"""
#         if not path.isfile(file_name):
#             raise IceFlix.UploadError

#         self.file_name = file_name
#         self.fd = open(file_name, 'rb')  # pylint: disable=consider-using-with

#     def receive(self, size, current=None):
#         """Lee un trozo del archivo de un tamaño size"""
#         chunk = self.fd.read(size)
#         return chunk

#     def close(self, current=None):
#         """Cierra el descriptor de archivo y su propia instancia del adaptador de objetos"""
#         self.fd.close()
#         current.adapter.remove(current.id)



if __name__ == "__main__":
    sys.exit(Client().main(sys.argv))