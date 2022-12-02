import cmd2
from cmd2 import (
    Bg,
    Fg,
    style,
)
from client import Client

class Client_cmd(cmd2.Cmd):

    prompt: style(bold=False)  #ponerle solo formato, es un mensaje que puede aparecer cada vez que el usuario mete un nuevo comando
    intro = style('Welcome to Iceflix!', fg=Fg.BLUE, bold=True) + ' 😀'



if __name__ == '__main__':
    app = Client_cmd()
    app.cmdloop()