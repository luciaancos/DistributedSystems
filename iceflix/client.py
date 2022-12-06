#!/usr/bin/env python3
import logging
import sys
import getpass
from hashlib import sha256
import threading
import time
from client_cmd import Client_cmd

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

class Client(Ice.Application):
    def __init__(self):
        self.main_obj = None # el main no va a cambiar
        self.user = ""
        self.password_hash = ""
        self.token = "" 
        self.history = [] #lista de strings que obtenemos en la ultima busqueda
        self.history_media = [] #lusta de objetos media que obtenemos en la ultima busqueda

    def run(self, argv):

        comm = self.communicator()
        adapter = comm.createObjectAdapterWithEndpoints("ClientAdapter", "tcp")
        client_cmd = Client_cmd()
        main_proxy = self.connect() #He modificado el metodo connect para que me devuelva el proxy del main y así poder pasarlo como argumento
        threading.Thread(target=client_cmd.cmdloop(), args= main_proxy).start()
        comm.waitForShutdown()
        self.connect()


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

    def connect(self):
        if self.client.main_obj is not None:
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
                
                
    def log_in(self):
        if self.user != "":
            print("There is a user already loggin, please try to log out if you want to change.")
            return -1

        if self.main_obj is None:
            print("First yo have to connect")
            return -1
            
        self.user = input("Introduce the user name: ")
        password = getpass.getpass(prompt='ntrodice the password: ')
        self.password_hash = sha256(password.encode()).hexdigest()
        try:
            authenticator = self.main_obj.getAuthenticator()
            
        except(Ice.ObjectNotExistException,IceFlix.TemporaryUnavailable):
            logging.error("Sorry, the autentificacion service is temporary unavailable")
            return -1
                
        try:
            self.token = authenticator.refreshAuthorization(self.user, self.password_hash)
            self.user = authenticator.whois(self.token)
        except IceFlix.Unauthorized:
            logging.error("Invalid user/password")
        else:   
            print("Successfully loged in. Enjoy!")
        return 0

    def admin_login(self):
        try:
            authenticator = self.main_obj.getAuthenticator()
            
        except(Ice.ObjectNotExistException,IceFlix.TemporaryUnavailable):
            logging.error("Sorry, the autentificacion service is temporary unavailable")
            return -1
        else:
            admin_token = getpass.getpass(prompt='Please write your admin token:')
            isAdmin = authenticator.isAdmin(admin_token)
            if(isAdmin):
                self.token = admin_token
                logging.info("Successfully loged in. Enjoy!")
            else:
                logging.error("You are not an admin")

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
        try:
            catalog = self.main_obj.getCatalog()
            print("ESTE ES EL CATALOGO")
            print(catalog)
        except(Ice.ObjectNotExistException,IceFlix.TemporaryUnavailable):
            logging.error("Sorry, the catalog service is temporary unavailable")
        else:
        
            nameorTag = input("\Would you like to search by name or by tags? Please write name or tag:").lower()

            try:
                #por nombre
                if nameorTag == "name":
                    exact = bool(input("Would you like to make an exact search? Please write yes or no:").lower()=="yes") #si no es ni si no no volver a preguntar?????????
                    name = input("\nWrite the title to want to search:")

                    self.history = catalog.getTilesByName(name, exact)
                    self.view_last_search(catalog)


                #por tags
                elif nameorTag == "tag":
                    tags = input("\nIntroduce the tags you want to search, please leave a blanck between them:").split()
                    includeAllTags = bool(input("\nWould yo like to obtain media that include all the tags? Write yes or no:").lower() == "yes")
                    try:
                        self.history = catalog.getTilesByTags(tags, includeAllTags, self.token)
                        self.view_last_search(catalog)
                    except IceFlix.Unauthorized:
                        logging.error("Incorrect user or password")
                    except(Ice.ObjectNotExistException,IceFlix.TemporaryUnavailable):
                        logging.error("Sorry, the catalog service is temporary unavailable")
                else:
                    print("Sorry, you have introduced an incorrect option") #deberia volver a dar opcion de introducirla???????????????????????
        
            except IceFlix.WrongMediaId as e:
                    logging.error("provided media ID is not found", str(e))

    def view_last_search(self): #history es lista de strings
        if len(self.history == 0):
            logging.error("\nNo media found.")

        else:
            try:
                catalog = self.main_obj.getCatalog()
            except(Ice.ObjectNotExistException,IceFlix.TemporaryUnavailable):
                logging.error("Sorry, the catalog service is temporary unavailable")
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

    def select_last_search(self):
        self.view_last_search()
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
        
        return self.history_media[selected] #devuelve el objeto entero seleccionado
            


    def edit_catalog(self,selected):
        try:
            catalog = self.main_obj.getCatalog()
        except(Ice.ObjectNotExistException,IceFlix.TemporaryUnavailable):
            logging.error("Sorry, the catalog service is temporary unavailable")
        else:
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
                        catalog.remove_tags_tile(selected.mediaqId, tags, self.token)
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
    
    def download_media(self):
        try:
            file_service = self.main_obj.getFileService()
        except IceFlix.TemporaryUnavailable:
            logging.error("The file service is not available")

        else:
            selected = self.select_last_search()
            try:
                file_handler =file_service.openFile(selected.mediaId, self.token)
            except IceFlix.Unauthorized:
                logging.error("Provided user token is wrong")
            except IceFlix.WrongMediaId:
                logging.error("Media id can not be found")
            else:
                file_handler.receive() #HASTA CUANDO RECIBO Y DONDE LO GUARDO?????????????????????????????????????????????
        

    def request_new_token(self): #llamar cada vez que sale la excepcion de unauthorised
        try:
            authenticator = self.main_obj.getAuthenticator()    
        except(Ice.ObjectNotExistException,IceFlix.TemporaryUnavailable):
            logging.error("Sorry, the autentificacion service is temporary unavailable")
            return -1
                
        try:
            self.token = authenticator.refreshAuthorization(self.user, self.password_hash)
        except IceFlix.Unauthorized:
            logging.error("Invalid user/password")
        return 0



    #ADMIN!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!      

    def add_user(self):
        user = input("\nIntroduce the user name: ")
        password = input("\nIntroduce the user password: ")
        password_hash = sha256(password.encode()).hexdigest()
        try:
            authenticator = self.main_obj.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            logging.error("The authentication service is not available")
        
        if authenticator.ice_isA('::IceFlix::Authenticator') == False:
            print("The proxy is not an authenticator")
        
        try:
            authenticator.addUser(user, password_hash, self.token)
            print("The user has been added")
        except IceFlix.Unauthorized:
                logging.error('Provided authentication token is wrong')
    
    def delete_user(self):
        user = input("\nIntroduce the user name you want to delete")
        try:
            authenticator = self.main_obj.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            logging.error("The authentication service is not available")
        
        if authenticator.ice_isA('::IceFlix::Authenticator') == False:
            print("The proxy is not an authenticator")

        try:
            authenticator.removeUser(user, self.token)
            print("The user has been removed")
        except IceFlix.Unauthorized:
            logging.error('Provided authentication token is wrong')

    def rename_media(self):
        try:
            catalog = self.main_obj.getCatalog()
        except(Ice.ObjectNotExistException,IceFlix.TemporaryUnavailable):
            logging.error("Sorry, the catalog service is temporary unavailable")
        
        print("Select the one you would like to change:")
        selected = self.select_last_search()
        new_name = input("Write the new name please: ")
        try:
            catalog.renameTile(selected.mediaId, new_name, self.token) #self token porque esto va con el admin y hay que pedirselo antes de entrar
            selected.info.name = new_name
            print("Name changed successfuly")
        except IceFlix.Unauthorized:
            logging.error("Provided user token is wrong")
        except IceFlix.WrongMediaId:
            logging.error("Media id can not be found")
            
    def upload_media(self):
        comm = self.communicator()
        file_name = input("Write the file route:")
        fu_servant = FileUploaderServant(file_name)
        adapter = comm.createObjectAdapterWithEndpoints("FileAdapter", "tcp")
        proxy = adapter.add(fu_servant, comm.stringToIdentity("FileUploader"))
        
        try:
            file_service = self.main_obj.getFileService()
        except IceFlix.TemporaryUnavailable:
            logging.error("File service unavailable")
        else:
            try:
                file_service.uploadFile(fu_servant, self.token)
                logging.info("The file has been uploades successfully")
            except IceFlix.Unauthorized:
                logging.error("Provided user token is wrong")

    def delete_media(self):
        try:
            file_service = self.main_obj.getFileService()
        except IceFlix.TemporaryUnavailable:
            logging.error("File service unavailable")
        else:
            print("Select the media you want to delete") #ESTO SOLO LE DEJA BORRAR DE L AULTIMA BUSQUEDA
            selected = self.select_last_search() #falta pasarle el catalog
            try:
                file_service.removeFile(selected.mediaID, self.token)
            except IceFlix.Unauthorized:
                logging.error("Provided user token is wrong")
            except IceFlix.WrongMediaId:
                logging.error("Media id can not be found") 


class FileUploaderServant(IceFlix.FileUploader):
    def __init__(self, file_name):
        self.file_name = file_name
        try:
            self.file_descriptor = open(file_name,"rb") #r = red, b = binary
        except FileNotFoundError:
            logging.error("File not found")

    def receive(self, size): 
        received = self.file_descriptor.read(size)
        return received

    def close(self):
        self.file_descriptor.close()


if __name__ == "__main__":
    sys.exit(Client().main(sys.argv))
