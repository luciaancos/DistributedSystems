#!/usr/bin/env python3
import cmd
from colorama import Style, Fore
class Client_cmd(cmd.Cmd):

    intro = Style.BRIGHT+ Fore.LIGHTMAGENTA_EX +  'Welcome to Iceflix! 😀' + Style.NORMAL + Fore.BLACK + '\nWrite "help" or "?" to see the options:'
    

    def do_connect(self, _):
        "Connects with main"
        self.client.connect()

    #tengo que hacer de desconectar??

    def do_login(self, _):
        "Logs the user"
        self.client.log_in()
    
    def do_logout(self, _):
        "Logs out the user"
        self.client.log_out()

    def do_search_in_catalog(self, _):
        "Searchs in catalog"
        self.client.catalog_search()
        #mirar aqui lo de busqueda anonima y comprobar si esta conectado 

    def do_view_last_search(self, _):
        "View the last history search"
        self.client.view_last_search()
        #comprobar conexion
        #hay que estas autenticado???????????

    def do_select_from_history(self, _):
        "Select media from last search"
        self.client.select_last_search()

    def do_download_media(self, _):
        "Download media"
        self.client.select_last_search()
        self.client.download_media()


    def do_admins_menu(self, _):
        "Shows the options of the admin"
        if self.client.main_obj is None:
            print("First you have to connect.")
        else:

            self.client.admin_login()

            #pedir el token o como se hace este login?
            #cuando pedimos el token isAdmin, y el nombre???????????????? el admin no tiene nombre

            while True:
                print('¿What would yo like to do?')
                print('1. Add user')
                print('2. Remove user')
                print('3. Change the name of a tile')
                print('4. Upload a tile')
                print('5. Remove a tile')
                print('6. Exit administrator mode')

                option = input()

                if option == '1':
                    self.client.add_user()

                elif option == '2':
                    self.client.delete_user()

                elif option == '3':
                    self.client.rename_media() 
                elif option == '4':
                    self.client.upload_file()
                
                elif option == '5':
                    self.client.delete_media()

                elif option == '6':
                    break

                else:
                    print("Incorrect option, please try again")
    

if __name__ == '__main__':
    # app = Client_cmd()
    # app.cmdloop()