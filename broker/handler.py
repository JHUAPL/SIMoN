import zmq
import time
import json
from threading import Thread, Event
from queue import Queue, Empty
import pymongo
import sys
import logging


class Broker:

    def __init__(self):
        """
        constructor for the broker
        """

        self.status = 'booting'
        self.pub_queue = Queue()
        with open('/opt/config.json') as models_file:
            models = json.load(models_file)
        self.models = {model: {} for model in models['models']}
        self.model_tracker = set()
        self.incstep = 1
        self.max_incstep = 50
        self.initial_year = 2016
        self.boot_timer = 60 # units: seconds
        self.watchdog_timer = 60 # units: seconds
        self.client = None
        self.mongo_queue = Queue()
        self.broker_id = 'broker'

        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                            format='%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s')
        logging.info(self.models)

    def insert_into_mongodb(self, event):
        """
        gets messages from the Mongo queue and inserts them into the database
        :param event: the shutdown event for managing threads
        :return: runs continuously until the shutdown event is set
        """

        try:
            self.client = pymongo.MongoClient('mongodb://mongodb:27017/')
            logging.info("connected to Mongo DB")
        except Exception as e:
            logging.error("failed to connect to Mongo DB")
            return False

        metadata_db = self.client[self.broker_id]
        while not event.is_set():
            try:
                message = self.mongo_queue.get(timeout=0.1)
                collection = message[0]
                messages_col = metadata_db[collection]
                payload = message[1]
                messages_col.insert_one(payload)
            except Empty:
                continue

    def send_status(self, event):
        """
        creates a status message and puts it into the publish queue
        :param event: the shutdown event for managing threads
        :return: runs continuously until the shutdown event is set
        """

        while not event.is_set():
            time.sleep(1)
            message = {}
            message['source'] = self.broker_id
            message['time'] = time.time()
            message['signal'] = 'status'
            message['status'] = self.status
            message['incstep'] = self.incstep
            message['initial_year'] = self.initial_year
            message['current_year'] = self.incstep + self.initial_year
            self.pub_queue.put(message)

    def pub(self, event):
        """
        publishes messages to the models, via the forwarder's SUB
        :param event: the shutdown event for managing threads
        :return: runs continuously until the shutdown event is set, then closes its zmq socket
        """

        context = zmq.Context()
        sock = context.socket(zmq.PUB)
        sock.setsockopt(zmq.LINGER, 1000)
        sock.connect('tcp://broker:5555')
        while not event.is_set():
            try:
                message = self.pub_queue.get(timeout=0.1)
            except Empty:
                continue
            logging.info(json.dumps(message))
            sock.send_json(message)

        sock.close()
        context.term()

    def sub(self, event):
        """
        receives messages from the models, via the forwarder's PUB
        :param event: the shutdown event for managing threads
        :return: runs continuously until the shutdown event is set, then closes its zmq socket
        """

        context = zmq.Context()
        sock = context.socket(zmq.SUB)
        sock.setsockopt(zmq.SUBSCRIBE, b"")
        sock.setsockopt(zmq.RCVTIMEO, 0)
        sock.setsockopt(zmq.LINGER, 1000)
        sock.connect('tcp://broker:5556')
        while not event.is_set():
            try:
                message = sock.recv_json()
            except zmq.ZMQError:
                continue
            logging.info(json.dumps(message))
            if message.get('source') in self.models and message.get('signal') == 'status':
                self.models[message.get('source')] = message
                self.model_tracker.add(message.get('source'))
            if message.get('signal') == 'data':
                self.mongo_queue.put(('sub', message))

        sock.close()
        context.term()

    def forwarder(self, event):
        """
        acts as a proxy between models by pushing messages received by the broker's SUB to the broker's PUB
        :param event: the shutdown event for managing threads
        :return: runs continuously until the shutdown event is set, then closes its zmq sockets
        """

        logging.info("started forwarder")
        context = zmq.Context()

        frontend = context.socket(zmq.SUB)
        frontend.setsockopt(zmq.SUBSCRIBE, b"")
        frontend.setsockopt(zmq.RCVTIMEO, 0)
        frontend.setsockopt(zmq.LINGER, 1000)
        frontend.bind('tcp://*:5555')

        backend = context.socket(zmq.PUB)
        backend.setsockopt(zmq.LINGER, 1000)
        backend.bind('tcp://*:5556')

        logging.info("listening in forwarder")
        while not event.is_set():
            try:
                message = frontend.recv_json()
                logging.debug("received message in forwarder")
                backend.send_json(message)
                logging.debug("sent message in forwarder")
            except zmq.ZMQError:
                continue

        logging.critical("forwarder is shutting down")
        frontend.close()
        backend.close()
        context.term()

    def watchdog(self, event):
        """
        verifies that every model is running by receiving its status messages. Sets the broker's status to 'booted'
        once it has received a status message from every model, and sets the shutdown event if it does not hear from
        one of the models within the timeout interval
        :param event: the shutdown event for managing threads
        :return: runs continuously until the shutdown event is set
        """

        while not event.is_set():
            for i in range(self.boot_timer if self.status == 'booting' else self.watchdog_timer):
                time.sleep(1)
                if self.model_tracker == set(self.models.keys()):
                    self.status = 'booted'
                    self.model_tracker.clear()
                    break
            else:
                missing_models = set(self.models.keys()) - self.model_tracker
                logging.critical(f"Timed out waiting for {missing_models}{' to initialize' if self.status == 'booting' else ''}")
                logging.critical(f"Broker will shut down now, current time: {time.ctime()}")
                event.set()

    def send_increment_pulse(self, event):
        """
        continuously checks the statuses of the models, then puts an increment pulse message into the publish queue
        once all of the models are ready to receive it
        :param event: the shutdown event for managing threads
        :return: runs continuously until the shutdown event is set
        """

        while not event.is_set():
            time.sleep(1)

            # check to send an increment pulse
            for model, status in self.models.items():
                if status.get('status') != 'ready' or status.get('incstep') != self.incstep:
                    break
            else:
                if self.incstep > self.max_incstep and self.mongo_queue.empty():
                    logging.critical(f"successfully finished last increment {self.max_incstep}")
                    logging.critical(f"Broker will shut down now, current time: {time.ctime()}")
                    event.set()
                else:
                    logging.info(f"sending increment pulse {self.incstep}")
                    message = {}
                    message['source'] = self.broker_id
                    message['time'] = time.time()
                    message['signal'] = 'increment'
                    message['status'] = self.status
                    message['incstep'] = self.incstep
                    message['year'] = self.incstep + self.initial_year
                    self.pub_queue.put(message)
                    self.incstep += 1

    def run(self):
        """
        the main thread of the broker. Launches all sub threads
        :return: runs continuously until the shutdown event is set
        """

        shutdown = Event()

        forwarder_thread = Thread(target=self.forwarder, args=(shutdown,))
        forwarder_thread.start()

        subscribe_thread = Thread(target=self.sub, args=(shutdown,))
        subscribe_thread.start()

        publish_thread = Thread(target=self.pub, args=(shutdown,))
        publish_thread.start()

        status_thread = Thread(target=self.send_status, args=(shutdown,))
        status_thread.start()

        watchdog_thread = Thread(target=self.watchdog, args=(shutdown,))
        watchdog_thread.start()

        increment_pulse_thread = Thread(target=self.send_increment_pulse, args=(shutdown,))
        increment_pulse_thread.start()

        mongo_thread = Thread(target=self.insert_into_mongodb, args=(shutdown,))
        mongo_thread.start()

        try:
            while not shutdown.is_set():
                time.sleep(1)
        except Exception as e:
            logging.critical(e)
        finally:
            shutdown.set()
            logging.critical("broker has shut down")


def main():
    broker = Broker()
    broker.run()


if __name__ == "__main__":
    main()
