"Client implementation"

#!/usr/bin/env python3
import logging


import random
import sys
import getpass
from hashlib import sha256
import threading
import time
import cmd
from colorama import Style, Fore

import Ice
import IceStorm

try:
    import IceFlix  # pylint:disable=import-error

except ImportError:
    import os
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix


# pylint: disable=C0103
# pylint: disable=W0613
# pylint: disable=E1101
#because we can not change the names and arguments of the topic methods


class Announcer(IceFlix.Announcement):
    "Servant for announcement interface"
    def __init__(self):
        self.main_proxys = {}

    def announce(self, service_proxy, serviceId, current):
        "Saves all the main proxys that announce in the topic"
        if service_proxy.ice_isA('::IceFlix::Main'):

            self.main_proxys[service_proxy] = (time.time())


    def check_dicc(self, client_cmd, servant):
        "Checks if the saved main proxys are availables"
        imprimir = False
        while True:
            copia = self.main_proxys.copy()
            if len(servant.main_proxys) == 0:
                print("Waiting for an available main service...")
                imprimir = True
                time.sleep(3)
            for proxy, timestamp in copia.items():
                if int(time.time()- timestamp) > 11:
                    copia.pop(proxy)
                    self.main_proxys = copia
                    break #queremos que se salga del for para que se copie y tenga la logitud nueva

                try:
                    proxy.ice_ping()
                   
                    if len(servant.main_proxys) == 1:
                        main_proxy = random.choice(list(servant.main_proxys.items()))
                        try:
                            main_obj = IceFlix.MainPrx.checkedCast(main_proxy[0])
                            client_cmd.main_obj = main_obj
                            main_proxy = main_proxy[0]
                            if imprimir == True:
                                print("You can continue.")
                                imprimir = False
                        except (Ice.ConnectionRefusedException, Ice.NoEndpointException):
                            break
                except (IceFlix.TemporaryUnavailable, Ice.ConnectionRefusedException):

                    if len(servant.main_proxys) != 0:
                        main_proxy = random.choice(list(servant.main_proxys.items()))
                        try:
                            main_obj = IceFlix.MainPrx.checkedCast(main_proxy[0])
                            client_cmd.main_obj = main_obj
                            main_proxy = main_proxy[0]
                            if imprimir == True:
                                print("You can continue.")
                                imprimir = False
                        except (Ice.ConnectionRefusedException, Ice.NoEndpointException):
                            break
                    else:
                        print("Waiting for an available main service...")
                        imprimir = True
                        time.sleep(3)


class AuthenChannel(IceFlix.UserUpdate):
    "Servant for UserUpdate interface"
    def newToken(self, user, token, service_id, current):
        "Prints info"
        print("The user: ", user, "has the new token: ", token, ".")
    def newUser(self, user, passwordHash, serviceId, current):
        "Prints info"
        print("A new user has been added: ", user, ".")
    def removeUser(self, user, serviceId, current):
        "Prints info"
        print("User ", user, "has been removed.")

class CatalogChannel(IceFlix.CatalogUpdate):
    "Servant for CatalogUpdate interface"
    def renameTile(self, mediaId, newName, serviceId, current):
        "Prints info"
        print(mediaId, "has chenged it name to", newName)
    def addTags(self, mediaId, user, tags, serviceId, current):
        "Prints info"
        print("The media: ", mediaId, "from user: ", user, "have added the tags: ", end=' ')
        print(', '.join(tags))
    def removeTags(self, mediaId, user, tags, serviceId, current):
        "Prints info"
        print("The media: ", mediaId, "from user: ", user, "have deleted the tags: ", end=' ')
        print(', '.join(tags))

class FileChannel(IceFlix.FileAvailabilityAnnounce):
    "Servant for FileAvailabilityAnnounce interface"
    def announceFiles(self, mediaIds, serviceId, current):
        "Prints info"
        print("Available files: ", end=' ')
        print(', '.join(mediaIds))

class Client(Ice.Application):
    """CLient Ice Aplication"""

    def run(self, args):
        comm = self.communicator()

        self.servant = Announcer()

    #reintento con el topic manager

        adapter = comm.createObjectAdapter("ClientAdapter")
        adapter.activate()
        proxy = adapter.addWithUUID(self.servant)
        topic_manager_str_prx = comm.propertyToProxy("topicManager")

        for i in range(3):
            try:
                topic_manager = IceStorm.TopicManagerPrx.checkedCast(topic_manager_str_prx)

                if not topic_manager:
                    print("Retrying to connect...")
                    raise RuntimeError("Invalid TopicManager proxy")
                else:
                    break
            except Ice.ConnectionRefusedException:
                logging.error("the topic is not available")
                break

        topic_name = "Announcements"
        try:
            topic = topic_manager.create(topic_name)
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve(topic_name)

        qos = {}
        topic.subscribeAndGetPublisher(qos, proxy)

        while True:
            if len(self.servant.main_proxys) != 0:

                main_proxy = random.choice(list(self.servant.main_proxys.items()))

                try:
                    main_obj = IceFlix.MainPrx.checkedCast(main_proxy[0])

                    if main_obj:
                        print("Successfully connected")

                        self.client_cmd = ClientCmd(main_obj, comm, adapter)

                        hilo_tiempo_main = threading.Thread(target=self.servant.check_dicc,
                                                            args=(self.client_cmd, self.servant,),
                                                            daemon=True)
                        hilo_tiempo_main.start()

                        threading.Thread(target=self.client_cmd.cmdloop, daemon=True).start()

                        break

                except (Ice.NoEndpointException, IceFlix.TemporaryUnavailable):
                    logging.error("Sorry, the main service is not available")

            else:
                print("Waiting for an available main service...")
                time.sleep(3)

        self.shutdownOnInterrupt()
        comm.waitForShutdown()
        topic.unsubscribe(proxy)


class ClientCmd(cmd.Cmd):
    """Class client using cmd"""

    intro = (Style.BRIGHT+ Fore.LIGHTMAGENTA_EX +  'Welcome to Iceflix! 😀' + Style.NORMAL +
             Fore.WHITE + '\nWrite "help" or "?" to see the options:')

    def __init__(self, main_obj, comm, adapter):
        super(ClientCmd, self).__init__()
        self.main_obj = main_obj
        self.comm = comm
        self.adapter = adapter
        self.user = ""
        self.password_hash = ""
        self.token = ""
        self.history = [] #list of strings of the last search
        self.history_media = [] #list of media objects of the last search
        self.define_prompt()


    def define_prompt(self):
        """Defines the format of the prompt message"""
        if self.main_obj is None:
            self.prompt = Style.NORMAL + Fore.WHITE + 'Disconnected'
        if self.main_obj is not None:
            if self.token == "":
                self.prompt = (Style.NORMAL + Fore.WHITE + '(Connected, '
                               + Style.NORMAL + Fore.WHITE + ' not logged) > ')
            else:
                self.prompt = (Style.NORMAL + Fore.WHITE + '(Connected, '
                               + Style.NORMAL + Fore.WHITE + 'user: ' + self.user + ') > ')



    def do_login(self, _):
        """Logs in the user"""
        if self.user != "":
            logging.error("There is a user already loggin, please try to log out first.")
            return

        if self.main_obj is None:
            logging.error("First yo have to connect")
            return
        try:
            authenticator = self.main_obj.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            logging.error("Sorry, the autentificacion service is temporary unavailable")
            return
        self.user = input("Introduce the user name: ")
        password = getpass.getpass(prompt='Introduce the password: ')
        self.password_hash = sha256(password.encode()).hexdigest()

        try:
            self.token = authenticator.refreshAuthorization(self.user, self.password_hash)
            self.user = authenticator.whois(self.token)
        except IceFlix.Unauthorized:
            logging.error("Incorrect user/password")
            self.user = ""
            return

        logging.info("Successfully loged in. Enjoy!")
        self.define_prompt()

    def do_logout(self, _):
        """Logs the user out"""
        if self.token == "":
            logging.error("You have not loged in yet")
            return
        self.user = ""
        self.password_hash = ""
        self.token = ""
        logging.info("Successful log out. See you soon!")
        self.define_prompt()

    def do_catalog_search(self, _):
        """Searchs in catalog by name or by tag"""

        self.history = []
        self.history_media = []

        try:
            catalog = self.main_obj.getCatalog()
        except IceFlix.TemporaryUnavailable:
            logging.error('Sorry, the catalog service is temporary unavailable')
            return

        while True:
            nameortag = input("Would you like to search by name or by tags? " +
                              "Please write name or tag:").lower()
            try:
                if nameortag == "name":
                    self.search_byname(catalog)
                    break
                elif nameortag == "tag":
                    self.search_bytag(catalog)
                    break
                else:
                    print("Sorry, you have introduced an incorrect option")
            except IceFlix.WrongMediaId:
                logging.error("provided media Id is not found")

    def search_byname(self, catalog):
        """Search media by name, allows anonimous search"""
        exact = bool(input("Would you like to make an exact search?" +
                           "Please write yes or no:").lower() == "yes")
        name = input("Write the title to want to search:")

        self.history = catalog.getTilesByName(name, exact)
        if self.token != "":
            self.view_last_search()
        else:
            print("Anonimous search just allows to see the mediaId:")
            for tile in self.history:
                print(tile)

    def search_bytag(self, catalog):
        """Search media by tag"""
        if self.token == "":
            logging.error("First you have to log in")
            return

        tags = input("\nIntroduce the tags you want to search," +
                     "please leave a blanck between them:").split()
        include_all_tags = bool(input("\nWould yo like to obtain media " +
                                      "that include all the tags? Write" +
                                      " yes or no:").lower() == "yes")
        while True:
            try:
                self.history = catalog.getTilesByTags(tags, include_all_tags, self.token)
                self.view_last_search()
                break
            except IceFlix.Unauthorized:
                self.request_new_token()
            except IceFlix.TemporaryUnavailable:
                logging.error('Sorry, the catalog service is temporary unavailable')
                return


    def do_view_last_search(self, _):
        """Shows media from last search"""
        self.view_last_search()

    def view_last_search(self): #history es lista de strings
        """Shows media from last search"""
        if (len(self.history) == 0):
            logging.info("No media found.")
            return

        try:
            catalog = self.main_obj.getCatalog()
        except IceFlix.TemporaryUnavailable:
            logging.error("Sorry, the catalog service is temporary unavailable")
            return
        self.history_media = []
        for tile in self.history: #for every component of the string list
            while True:
                try:
                    media = catalog.getTile(tile, self.token) #we get the media object
                    self.history_media.append(media) #history_media stores objects
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
        print("LAST SEARCH MEDIA:")
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
                return None
            else:
                return self.history_media[selected-1] #returns the selected media object

    def do_edit_catalog(self, _):
        """Edits the selected media of the catalog"""

        if (len(self.history) == 0):
            logging.info("\nNo media found. Please, first search media in the catalog."+
                         " As you are not in the admin mode you just have acces to the" +
                         " media searched before.")
            return
        try:
            catalog = self.main_obj.getCatalog()
        except IceFlix.TemporaryUnavailable:
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

            if option == 1:
                self.add_tag(catalog, selected)
                break

            elif option == 2:
                self.remove_tag(catalog, selected)
                break

            elif option == 3:
                break

    def add_tag(self, catalog, selected):
        """Adds tags to media"""
        while True:
            try:
                tags = input("Introduce the tags you want to add: ").lower().split()
                catalog.addTags(selected.mediaId, tags, self.token)
                logging.info("Tags added correctly")
                break
            except IceFlix.Unauthorized:
                self.request_new_token()
            except IceFlix.WrongMediaId:
                logging.error("Media id can not be found")
                return

    def remove_tag(self, catalog, selected):
        """Removes tags from media"""
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


    def do_download_media(self, _):
        """Downloads the selected media"""
        if (len(self.history) == 0):
            logging.info("\nNo media found. Please, first search media in the catalog."+
                         " As you are not in the admin mode you just have acces to the"+
                         " media searched before.")
            return
        try:
            file_service = self.main_obj.getFileService()
        except IceFlix.TemporaryUnavailable:
            logging.error("The file service is not available")
            return

        print("Introduce el media id you want to download:")
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
                received = file_handler.receive(1024, self.token)
                if len(received) == 0:
                    break
                file_descriptor.write(received)
        file_handler.close(self.token)


    def request_new_token(self):
        """Request a new token if it has been revoqued, we call this method everytime
           we catch the exception Unauthorised"""
        try:
            authenticator = self.main_obj.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            logging.error("Sorry, the autentificacion service is temporary unavailable")
            return

        try:
            self.token = authenticator.refreshAuthorization(self.user, self.password_hash)
        except IceFlix.Unauthorized:
            logging.error("Invalid user/password")
            return

    def do_admin_mode(self, _):
        """Acess to the admins cmd"""
        admin = AdminCmd(self.main_obj, self.comm, self.adapter)
        admin.cmdloop()

    def do_exit(self, _):
        """Exits from the cmd"""
        print("Exit...")
        print("press ctrl + c to finish")
        return True


class AdminCmd(cmd.Cmd):
    """Administrator cmd"""
    intro = Style.NORMAL + Fore.BLACK + '\nWelcome to the administrator mode'
    prompt = Style.NORMAL + Fore.BLACK + '(Admin mode) > '


    def __init__(self, main, comm, adapter):
        super(AdminCmd, self).__init__()
        self.main_obj = main
        self.comm = comm
        self.adapter = adapter
        self.admintoken = ""
        self.adminlogin()

    def adminlogin(self):
        """Logs in as an admin, with the admin token"""
        try:
            authenticator = self.main_obj.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            logging.error("Sorry, the autentificacion service is temporary unavailable")
            return
        else:
            self.admintoken = getpass.getpass(prompt='Please write your admin token:')
            is_admin = authenticator.isAdmin(self.admintoken)
            if is_admin:
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
        """Rename media introducind the media id"""
        try:
            catalog = self.main_obj.getCatalog()
        except IceFlix.TemporaryUnavailable:
            logging.error("Sorry, the catalog service is temporary unavailable")
            return

        mediaid_str = input("Introduce the mediaId you want to rename: ")
        new_name = input("Write the new name please: ")
        try:
            catalog.renameTile(mediaid_str, new_name, self.admintoken)
            logging.info("Name changed successfuly")
        except IceFlix.Unauthorized:
            logging.error("Provided user token is wrong")
        except IceFlix.WrongMediaId:
            logging.error("Media id can not be found")

    def do_upload_media(self, _):
        """Uploads the media that corresponds to the path, given as an input"""
        file_name = input("Write the file path: ")
        try:
            fu_servant = FileUploaderServant(file_name)
        except FileNotFoundError:
            logging.error("File not found")
            return

        proxy = self.adapter.addWithUUID(fu_servant)
        uploader_proxy = IceFlix.FileUploaderPrx.uncheckedCast(proxy)


        try:
            file_service = self.main_obj.getFileService()
        except IceFlix.TemporaryUnavailable:
            logging.error("File service unavailable")
        else:
            try:
                file_service.uploadFile(uploader_proxy, self.admintoken)
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
            mediaid_str = input("Introduce mediaId you want to delete: ")
            try:
                file_service.removeFile(mediaid_str, self.admintoken)
                logging.info("Successfully deleted")
            except IceFlix.Unauthorized:
                logging.error("Provided user token is wrong")
                return
            except IceFlix.WrongMediaId:
                logging.error("Media id can not be found")
                return

    def do_suscribeAuthenticatorChannel(self, _):
        "Suscribes to UserUpdates channel"

        print("Press 'q' + enter if you want to unsuscribe")

        servant = AuthenChannel()
        #self.adapter.activate()
        proxy = self.adapter.addWithUUID(servant)
        topic_manager_str_prx = self.comm.propertyToProxy("topicManager")
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(topic_manager_str_prx)

        if not topic_manager:
            raise RuntimeError("Invalid TopicManager proxy")

        topic_name = "UserUpdates"
        try:
            topic = topic_manager.create(topic_name)
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve(topic_name)

        qos = {}
        topic.subscribeAndGetPublisher(qos, proxy)
        while True:
            tecla = input()
            if tecla == 'q':
                # Salimos del método si el usuario pulsa 'q'
                topic.unsubscribe(proxy)
                break

    def do_suscribeCatalogChannel(self, _):
        "Suscribes to CatalogUpdates channel"
        print("Press 'q' + enter if you want to unsuscribe")

        servant = CatalogChannel()
        proxy = self.adapter.addWithUUID(servant)
        topic_manager_str_prx = self.comm.propertyToProxy("topicManager")
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(topic_manager_str_prx)

        if not topic_manager:
            raise RuntimeError("Invalid TopicManager proxy")

        topic_name = "CatalogUpdates"
        try:
            topic = topic_manager.create(topic_name)
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve(topic_name)

        qos = {}
        topic.subscribeAndGetPublisher(qos, proxy)

        while True:
            tecla = input()
            if tecla == 'q':
                # Salimos del método si el usuario pulsa 'q'
                topic.unsubscribe(proxy)
                break

    def do_suscribeFileChannel(self, _):
        "Suscribes to FileAvailabilityAnnounce channel"
        print("Press 'q' + enter if you want to unsuscribe")

        servant = FileChannel()
        proxy = self.adapter.addWithUUID(servant)
        topic_manager_str_prx = self.comm.propertyToProxy("topicManager")
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(topic_manager_str_prx)

        if not topic_manager:
            raise RuntimeError("Invalid TopicManager proxy")

        topic_name = "FileAvailabilityAnnounce"
        try:
            topic = topic_manager.create(topic_name)
        except IceStorm.TopicExists:
            topic = topic_manager.retrieve(topic_name)

        qos = {}
        topic.subscribeAndGetPublisher(qos, proxy)

        while True:
            tecla = input()
            if tecla == 'q':
                # Salimos del método si el usuario pulsa 'q'
                topic.unsubscribe(proxy)
                break

    def do_exit(self, _):
        """Exit from the admin mode"""
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

if __name__ == '__main__':#no se usa si se usa los configs
    sys.exit(Client().main(sys.argv))