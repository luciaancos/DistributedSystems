# MANUAL DE USUARIO

Para comenzar, tenemos que instalar el módulo y las dependecias. Para ello ejecutamos `pip intall -e .` , con esto conseguimos instalarnos lo que aparece en setup.cfg. Es preferible realizar esto en un entorno virtual.

Después para ejecutar, simplemente ejecutamos primero `./run_icestorm` y en otra términal `./run_client`, ya que está configurado para que setup.cfg, cli.py y run_client se comuniquen de forma que todo se ejecute correctamente. 

Cuando encuentra un main disponible se conecta, nos aparece un cmd, si escribimos 'help' o '?' veremos las opciones disponibles. Cuando el cliente está escribiendo la opción, se le permite autocompletar el nombre de dicha opción pulsando el tabulador. 

Tras seleccionar una de las opciones, hay que seguir los pasos que van apareciendo por pantalla para conseguir la funcionalidad solicitada.


Destacamos que una de estas opciones es el menu administrador, si la elegimos nos pedirá el adminToken y si este es correcto nos aparecerá otra cmd de administradores con nuevas opciones. Siempre podemos volver a la terminal del cliente seleccionando la opción exit.

Si se da el caso en el que nos hemos conseguido conectar a un main, pero después no es posible realizar la conexión con él, el programa automaticamente elige otro disponible. Si se queda sin ninguno disponible, esperará a que vuelva a poder conectarse y cuando lo consigue lo indica con el mensaje de "You can continue"

Si al pulsar Ctrl+C la terminal se queda inservible, utilizar el comando reset en vez de clear. Cómo comente por correo intenté solucionar este error pensando que era problema de colorama, pero debe ser por algo del cmd. Espero que no se tenga en cuenta como me respondísteis. 

Un detalle de la implementación es que en los métodos del cliente normal solo te deja ver y editar los objetos media de la última búsqueda, sin embargo en el modo administrador nos solicitará por pantalla el mediaId de cualquier objeto media que queramos manipular. Esto sigue la lógica de que el administrador tiene acceso a cualquier parte de IceFlix.


## Pruebas

Hay dos archivos dedicados a pruebas que simulan un servicio main, para ver si el cliente funcionaba correctamente [pruebas](https://github.com/luciaancos/lab_ssdd/blob/main/iceflix/main_prueba.py) , [pruebaconfig](https://github.com/luciaancos/lab_ssdd/blob/main/configs/main.config)

Se ejecuta con `python3 iceflix/main_prueba.py --Ice.Config=configs/main.config`

