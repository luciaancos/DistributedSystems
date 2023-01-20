"""Prueba announce Main."""
# pylint:disable=R0201
# pylint:disable=C0103
# pylint:disable=W0622
# pylint:disable=R0201
# pylint:disable=R0903
# pylint:disable=W0201
import sys
import time
import threading
import uuid
import os
import Ice  # pylint:disable=import-error

try:
    import IceFlix
    import IceStorm

except ImportError:
    Ice.loadSlice(os.path.join(os.path.dirname(__file__), "iceflix.ice"))
    import IceFlix  #pylint:disable=ungrouped-imports
    import IceStorm  #pylint:disable=ungrouped-imports


class MainPrueba(IceFlix.Announcement):
    """Sirviente para la interfaz IceFlix.Announcement"""

    def announce(self, proxy, service_id, current): 
        """Send proxy and service_id to the client"""
        if proxy.ice_isA('::IceFlix::Main'):
            print(f"Announce Main \n")

    def announce_main(self, publisher, proxy_main, id):
        """Announce Main"""
        while True:
            publisher.announce(proxy_main, id)
            time.sleep(9)


class Main(IceFlix.Main):
    """Servant"""

    def __init__(self):
        self.id_main = str(uuid.uuid4())


class MainApp(Ice.Application):
    """Run main ."""

    def __init__(self):
        super().__init__()
        self.proxy = None
        self.service_id = None
        self.servant_main = None
        self.servant_anunciador = None
        self.hilo_announcement = None

    def run(self, args):  # pylint:disable=R0914, too-many-statements
        """Run main ."""

        properties = self.communicator().getProperties()
        self.servant_main = Main()
        adapter = (self.communicator().createObjectAdapterWithEndpoints(
            "MainAdapter", properties.getProperty("MainAdapter.Endpoints")))
        adapter.activate()

        self.proxy = adapter.addWithUUID(self.servant_main)
        self.proxy = IceFlix.MediaCatalogPrx.uncheckedCast(self.proxy)
        self.service_id = self.servant_main.id_main
        ice_communicator = self.communicator()

        topic_manager_str = ice_communicator.propertyToProxy("TopicManager")
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(topic_manager_str)  

        if not topic_manager:
            raise RuntimeError("Invalid TopicManager proxy")

        topic_name = "Announcements"
        try:
            topic = topic_manager.create(topic_name)
        except IceStorm.TopicExists:  
            topic = topic_manager.retrieve(topic_name)

        self.publisher_servant = MainPrueba()
        announce = adapter.addWithUUID(self.publisher_servant)

        topic.subscribeAndGetPublisher({}, announce)
        publisher = topic.getPublisher()
        publisher = IceFlix.AnnouncementPrx.uncheckedCast((publisher))

        self.hilo_announcement = threading.Thread(
            target=self.publisher_servant.announce_main,
            args=(publisher, self.proxy, self.service_id),
            daemon=True)
        self.hilo_announcement.start()

        self.shutdownOnInterrupt()
        self.communicator().waitForShutdown()
        topic.unsubscribe(announce)

        return 0


if __name__ == '__main__':
    MAIN = MainApp()
    sys.exit(MAIN.main(sys.argv))