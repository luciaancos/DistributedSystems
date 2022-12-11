# MANUAL DE USUARIO

Para comenzar, tenemos que instalar el módulo y las dependecias. Para ello ejecutamos `pip intall -e .` , con esto conseguimos instalarnos lo que aparece en setup.cfg. Es preferible realizar esto en un entorno virtual.

Después para ejecutar, simplemente ejecutamos `./run_client`, ya que está configurado para que setup.cfg, cli.py y run_client se comuniquen de forma que todo se ejecute correctamente. 

Una vez ejecutamos el código, nos pedirá el proxy del main para poder conectarse dejando tres intentos al cliente. Cuando nos hemos conectado, nos aparece un cmd, si escribimos 'help' o '?' veremos las opciones disponibles. Cuando el cliente está escribiendo la opción, se le permite autocompletar el nombre de dicha opción pulsando el tabulador. 

Tras seleccionar una de las opciones, hay que seguir los pasos que van apareciendo por pantalla para conseguir la funcionalidad solicitada.


Destacamos que una de estas opciones es el menu administrador, si la elegimos nos pedirá el adminToken y si este es correcto nos aparecerá otra cmd de administradores con nuevas opciones. Siempre podemos volver a la terminal del cliente seleccionando la opción exit.

Un detalle de la implementación es que en los métodos del cliente normal solo te deja ver y editar los objetos media de la última búsqueda, sin embargo en el modo administrador nos solicitará por pantalla el mediaId de cualquier objeto media que queramos manipular. Esto sigue la lógica de que el administrador tiene acceso a cualquier parte de IceFlix.

# Template project for ssdd-lab

This repository is a Python project template.
It contains the following files and directories:

- `configs` has several configuration files examples.
- `iceflix` is the main Python package.
  You should rename it to something meaninful for your project.
- `iceflix/__init__.py` is an empty file needed by Python to
  recognise the `iceflix` directory as a Python module.
- `iceflix/cli.py` contains several functions to handle the basic console entry points
  defined in `python.cfg`.
  The name of the submodule and the functions can be modified if you need.
- `iceflix/iceflix.ice` contains the Slice interface definition for the lab.
- `iceflix/main.py` has a minimal implementation of a service,
  without the service servant itself.
  Can be used as template for main or the other services.
- `pyproject.toml` defines the build system used in the project.
- `run_client` should be a script that can be run directly from the
  repository root directory. It should be able to run the IceFlix
  client.
- `run_service` should be a script that can be run directly from the
  repository root directory. It should be able to run all the services
  in background in order to test the whole system.
- `setup.cfg` is a Python distribution configuration file for Setuptools.
  It needs to be modified in order to adeccuate to the package name and
  console handler functions.
