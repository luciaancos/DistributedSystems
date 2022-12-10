#!/usr/bin/env python3
import cmd
import getpass
from hashlib import sha256
import logging
from colorama import Style, Fore
import Ice

try:
    import IceFlix  # pylint:disable=import-error

except ImportError:
    import os
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix

LOG_FORMAT = '%(asctime)s - %(levelname)-7s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'

logger = logging.getLogger('CLIENT_APPLICATION')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)-7s - %(module)s:%(funcName)s:%(lineno)d - %(message)s')

# add formatter to ch
console_handler.setFormatter(formatter)

# add ch to logger
logger.addHandler(console_handler)



class ClientCmd(cmd.Cmd):
    """Class client using cmd"""

    intro = Style.BRIGHT+ Fore.LIGHTMAGENTA_EX +  'Welcome to Iceflix! 😀' + Style.NORMAL + Fore.BLACK + '\nWrite "help" or "?" to see the options:'

    def __init__(self, main_obj, comm):
        #### THIS IS THE LINE YOU FORGOT!!!!
        super(ClientCmd, self).__init__()
        self.main_obj = main_obj # el main no va a cambiar
        self.comm = comm
        self.user = ""
        self.password_hash = ""
        self.token = ""
        #self.admintoken = ""  PROBAR ESTOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
        self.history = [] #lista de strings que obtenemos en la ultima busqueda
        self.history_media = [] #lusta de objetos media que obtenemos en la ultima busqueda
        self.define_prompt()

    def define_prompt(self):
        """Defines the format of the prompt message"""
        if self.main_obj is None:
            self.prompt = Style.NORMAL + Fore.BLACK + 'Disconnected'
        if self.main_obj is not None:
            if self.token == "":
                self.prompt = Style.NORMAL + Fore.BLACK + '(Connected, ' + Style.NORMAL + Fore.BLACK + ' not logged) > '
            else:
                self.prompt = Style.NORMAL + Fore.BLACK + '(Connected, ' + Style.NORMAL + Fore.BLACK + 'user: ' + self.user + ') > '

    def do_login(self, _):
        """Logs in the user"""
        if self.user != "":
            print("There is a user already loggin, please try to log out if you want to change.")
            return

        if self.main_obj is None:
            print("First yo have to connect")
            return
        try:
            authenticator = self.main_obj.getAuthenticator()
        except(IceFlix.TemporaryUnavailable):
            logger.error("Sorry, the autentificacion service is temporary unavailable")
            return
        self.user = input("Introduce the user name: ")
        password = getpass.getpass(prompt='Introdice the password: ')
        self.password_hash = sha256(password.encode()).hexdigest()
        while True:
            try:
                self.token = authenticator.refreshAuthorization(self.user, self.password_hash)
                self.user = authenticator.whois(self.token)
                break
            except IceFlix.Unauthorized:
                self.request_new_token()
            
        print("Successfully loged in. Enjoy!")
        self.define_prompt()

    def do_logout(self, _):
        """Logs the user out"""
        if self.token == "":
            print("You have not loged in yet")
            return
        self.user = ""
        self.password_hash = ""
        self.token = ""
        print("Successful log out. See you soon!")
        self.define_prompt()

    def do_catalog_search(self, _):
        """Searchs in catalog by name or by tag"""
        
        #CADA VEZ QUE BUSQUEMOS ALGO RESETEAR LISTAS
        self.history = []
        self.history_media = []

        try:
            catalog = self.main_obj.getCatalog()
            print("ESTE ES EL CATALOGO")
            print(catalog)
        except(IceFlix.TemporaryUnavailable):
            logger.error("Sorry, the catalog service is temporary unavailable")
            return

        nameortag = input("\Would you like to search by name or by tags? Please write name or tag:").lower()
        try:
            #por nombre
            if nameortag == "name":
                exact = bool(input("Would you like to make an exact search? Please write yes or no:").lower() == "yes") #si no es ni si no no volver a preguntar?????????
                name = input("\nWrite the title to want to search:")

                self.history = catalog.getTilesByName(name, exact)
                self.view_last_search()


            #por tags
            elif nameortag == "tag":
                if self.token == "":
                    logger.error("First you have to log in")
                    return

                tags = input("\nIntroduce the tags you want to search, please leave a blanck between them:").split()
                include_all_tags = bool(input("\nWould yo like to obtain media that include all the tags? Write yes or no:").lower() == "yes")
                while True:
                    try:
                        self.history = catalog.getTilesByTags(tags, include_all_tags, self.token)
                        self.view_last_search()
                        break
                    except IceFlix.Unauthorized:
                        self.request_new_token()
                    except(IceFlix.TemporaryUnavailable):
                        logger.error("Sorry, the catalog service is temporary unavailable")
                        return
            else:
                print("Sorry, you have introduced an incorrect option") #deberia volver a dar opcion de introducirla???????????????????????
        except IceFlix.WrongMediaId as e:
            logger.error("provided media ID is not found", str(e))

    def do_view_last_search(self, _):
        """Shows media from last search"""
        self.view_last_search()

    def view_last_search(self): #history es lista de strings
        """Shows media from last search"""
        if (len(self.history) == 0):
            logger.error("\nNo media found.")

        else:
            try:
                catalog = self.main_obj.getCatalog()
            except(IceFlix.TemporaryUnavailable):
                logging.error("Sorry, the catalog service is temporary unavailable")
                return
            self.history_media = []
            for tile in self.history: #para cada componente de la lista de strings
                while True:
                    try:
                        media = catalog.getTile(tile, self.token) #conseguimos el objeto media
                        self.history_media.append(media) #en history media metemos objetos media
                        break
                    except IceFlix.WrongMediaId:
                        logging.error("The id is incorrect")
                        return
                    except IceFlix.TemporaryUnavailable:
                        logging.error("The requested item is currently unavailable")
                        return
                    except IceFlix.Unauthorized:
                        self.request_new_token()

            counter = 1
            for media in self.history_media:
                print(str(counter) + ': ' + media.info.name)
                counter += 1

    def do_select_from_lastsearch(self, _):
        """Allows to select media from the last search"""
        self.select_last_search()

    def select_last_search(self):
        """Allows to select media from the last search"""
        self.view_last_search()
        while True:
            try:
                selected = int(input("\nSelect the number of the title: "))
                if selected > len(self.history_media)+1 or selected < 0:
                    raise ValueError

            except ValueError:
                logging.error("Incorrect option, try again please")
                return
            else:
                return self.history_media[selected-1] #devuelve el objeto entero seleccionado

    def do_edit_catalog(self, _):
        """Edits the selected media of the catalog"""
        if (len(self.history) == 0):
            logging.error("\nNo media found.")
            return
        try:
            catalog = self.main_obj.getCatalog()
        except(IceFlix.TemporaryUnavailable):
            logging.error("Sorry, the catalog service is temporary unavailable")
            return

        selected = self.select_last_search()
        while True:
            print('¿What would yo like to do with? (' + selected.info.name + ')')
            print('1. Add tags')
            print('2. Remove tags')
            print('3. Exit')

            try:
                option = int(input())
                if option > 3 or option < 1:
                    raise ValueError
            except ValueError:
                logging.error("Incorrect option, try again please")
                return

            if option == 1:
                while True:
                    try:
                        tags = input("Introduce the tags you want to add: ").lower().split()
                        catalog.addTags(selected.mediaId, tags, self.token)
                        logger.info("Tags added correctly")
                        break
                    except IceFlix.Unauthorized:
                        self.request_new_token()
                    except IceFlix.WrongMediaId:
                        logging.error("Media id can not be found")
                        return
                break

            elif option == 2:
                while True:
                    try:
                        tags = input("Introduce the tags you want to remove: ").lower().split()
                        catalog.removeTags(selected.mediaId, tags, self.token)
                        logging.info("Tags removed correctly")
                        break
                    except IceFlix.Unauthorized:
                        self.request_new_token()
                    except IceFlix.WrongMediaId:
                        logging.error("Media id can not be found")
                        return
                break

            elif option == 3:
                break

    def do_download_media(self, _):
        """Downloads the selected media"""
        try:
            file_service = self.main_obj.getFileService()
        except IceFlix.TemporaryUnavailable:
            logging.error("The file service is not available")
            return

        selected = self.select_last_search()
        while True:
            try:
                file_handler = file_service.openFile(selected.mediaId, self.token)
                break
            except IceFlix.Unauthorized:
                self.request_new_token() #refresh token
            except IceFlix.WrongMediaId:
                logging.error("Media id can not be found")
                return
        with open(selected.mediaId, 'wb') as file_descriptor:
            while True:
                received = file_handler.receive(1024) #HASTA CUANDO RECIBO Y DONDE LO GUARDO?????????????????????????????????????????????
                if len(received) == 0:
                    break
                file_descriptor.write(received)
        file_handler.close()#metoo del slice

    def request_new_token(self):#llamar cada vez que sale la excepcion de unauthorised
        """Request a new token if it has been revoqued"""
        try:
            authenticator = self.main_obj.getAuthenticator()
        except(IceFlix.TemporaryUnavailable):
            logging.error("Sorry, the autentificacion service is temporary unavailable")
            return

        try:
            self.token = authenticator.refreshAuthorization(self.user, self.password_hash)
        except IceFlix.Unauthorized:
            logging.error("Invalid user/password")

    def do_adminMode(self, _):
        if self.token == "":
            print("First you have to login")
            return
        admin = Admin_cmd(self.main_obj, self.comm)
        admin.cmdloop()


   #--------------------------------------------------PONER EN TODOS LOS METODOS QUE PRIMERO LOGIN----------------------------------------- 

    

    def do_exit(self, _):
        """Exits from the cmd"""
        print("Saliendo...")
        self.comm.waitForShutdown()
        return True


class Admin_cmd(cmd.Cmd):
    intro = Style.NORMAL + Fore.BLACK + '\nWelcome to the administrator mode'

    #PONER EN TODOS LOS METODOS QUE PRIMERO TIENE QUE HACER EL LOGIN

    def __init__(self, main, comm):
        super(Admin_cmd, self).__init__()
        self.main_obj = main
        self.comm = comm
        self.admintoken = ""
        self.adminlogin()

    def adminlogin(self):
        """Logs in as an admin, with the admin token"""
        try:
            authenticator = self.main_obj.getAuthenticator()
        except(IceFlix.TemporaryUnavailable):
            logging.error("Sorry, the autentificacion service is temporary unavailable")
            return
        else:
            self.admintoken = getpass.getpass(prompt='Please write your admin token:')
            is_admin = authenticator.isAdmin(self.admintoken)
            print(is_admin)
            if(is_admin):
                print("aqui dentro")
                print("Successfully loged in. Enjoy!")
            else:
                logging.error("You are not an admin")

    def do_add_user(self, _):
        """Add a user to the persistence of the Athenticator service"""
        user = input("\nIntroduce the user name: ")
        password = input("\nIntroduce the user password: ")
        password_hash = sha256(password.encode()).hexdigest()
        try:
            authenticator = self.main_obj.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            logging.error("The authentication service is not available")

        try:
            authenticator.addUser(user, password_hash, self.admintoken)
            print("The user has been added")
        except IceFlix.Unauthorized:
            logging.error('Provided authentication token is wrong')

    def do_delete_user(self, _):
        """Deletes a user from the persistence of the Athenticator service"""
        user = input("\nIntroduce the user name you want to delete")
        try:
            authenticator = self.main_obj.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            logging.error("The authentication service is not available")

        try:
            authenticator.removeUser(user, self.admintoken)
            print("The user has been removed")
        except IceFlix.Unauthorized:
            logging.error('Provided authentication token is wrong')

    def do_rename_media(self, _):
        """Rename media that the client have searched"""
        try:
            catalog = self.main_obj.getCatalog()
        except(IceFlix.TemporaryUnavailable):
            logging.error("Sorry, the catalog service is temporary unavailable")

        print("Select the one you would like to change:")
        selected = self.select_last_search()
        new_name = input("Write the new name please: ")
        try:
            catalog.renameTile(selected.mediaId, new_name, self.admintoken)#self token porque esto va con el admin y hay que pedirselo antes de entrar
            selected.info.name = new_name
            print("Name changed successfuly")
        except IceFlix.Unauthorized:
            logging.error("Provided user token is wrong")
        except IceFlix.WrongMediaId:
            logging.error("Media id can not be found")

    def do_upload_media(self, _):
        """Uploads the media that corresponds to the path, given as an input"""
        #comm = self.communicator()
        file_name = input("Write the file route:")
        try:
            fu_servant = FileUploaderServant(file_name)
        except FileNotFoundError:
            logging.error("File not found")
            return
        adapter = self.comm.createObjectAdapterWithEndpoints("FileAdapter", "tcp") #en el constructor del cmd
        proxy = adapter.add(fu_servant) #usar addWithUUID

        try:
            file_service = self.main_obj.getFileService()
        except IceFlix.TemporaryUnavailable:
            logging.error("File service unavailable")
        else:
            try:
                file_service.uploadFile(fu_servant, self.admintoken) #le tengo que pasar el proxy y hacer unchequed cast
                logging.info("The file has been uploades successfully")
            except IceFlix.Unauthorized:
                logging.error("Provided user token is wrong")

    def do_delete_media(self, _):
        """Deletes the selected media from last search"""
        try:
            file_service = self.main_obj.getFileService()
        except IceFlix.TemporaryUnavailable:
            logging.error("File service unavailable")
        else:
            print("Select the media you want to delete")
            selected = self.select_last_search()#falta pasarle el catalog
            try:
                file_service.removeFile(selected.mediaID, self.admintoken)
            except IceFlix.Unauthorized:
                logging.error("Provided user token is wrong")
            except IceFlix.WrongMediaId:
                logging.error("Media id can not be found")
    

    def do_exit(self, _):
        self.admintoken = ""
        print("saliendo del admin")
        return True


class FileUploaderServant(IceFlix.FileUploader):
    """Servant of the FileUploader interface"""
    def __init__(self, file_name):
        self.file_name = file_name
        self.file_descriptor = open(file_name, "rb") #r = read, b = binary

    def receive(self, size, current=None):
        """Recibes bytes reading from the file descriptor"""
        received = self.file_descriptor.read(size)
        return received

    def close(self, current=None):
        """Closes the file descriptor and deletes the object adapter"""
        self.file_descriptor.close()
        current.adapter.remove(current.id) 