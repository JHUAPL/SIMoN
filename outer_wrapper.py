import zmq
import json
from jsonschema import validate, ValidationError
import time
import glob
from threading import Thread, Event
from queue import Queue, Full, Empty
from abc import ABC, abstractmethod
import os
import sys
import logging
import networkx as nx
from collections import defaultdict
import base64


class Graph(nx.DiGraph):

    def __init__(self, filename=None):
        super().__init__()
        self.functions = {"simple_sum": self.simple_sum, "distribute_uniformly": self.distribute_uniformly, "distribute_by_area": self.distribute_by_area}
        self.default_aggregator = self.simple_sum
        self.default_disaggregator = self.distribute_by_area
        if filename:
            with open(filename, mode='r') as json_file:
                data = json.load(json_file)
            for node in data['nodes']:
                self.add_node(node['id'], name=node.get('name'), type=node.get('type'), shape=node.get('shape'), area=node.get('area'))
            for edge in data['links']:
                self.add_edge(edge['source'], edge['target'], a=edge.get('a'), d=edge.get('d'))

    def simple_sum(self, values):
        """
        aggregator for an instance graph
        :param values: a list of values
        :return: a scalar value, the summation of the values
        """
        return sum(values)

    def distribute_uniformly(self, value, instance, child_granularity):
        """
        disaggregator for an instance graph
        :param value:
        :param instance:
        :param child_granularity: the intended granularity of the transformation. the child node of the instance in the abstract graph
        :return:
        """
        if instance not in self.nodes:
            logging.critical("instance {} not in instance graph".format(instance))
            return {}
        children = [child for child in self.successors(instance) if self.nodes[child]['type'] == child_granularity]
        mean = value / len(children)
        distributed = {child: mean for child in children}
        return distributed

    def distribute_by_area(self, value, instance, child_granularity):
        """
        disaggregator for an instance graph
        :param value:
        :param instance:
        :param child_granularity: the intended granularity of the transformation. the child node of the instance in the abstract graph
        :return:
        """
        if instance not in self.nodes:
            logging.critical("instance {} not in instance graph".format(instance))
            return {}
        children = [child for child in self.successors(instance) if self.nodes[child]['type'] == child_granularity]
        parent_area = self.nodes[instance]["area"]
        distributed = {child: value * self.nodes[child]["area"] / parent_area for child in children}
        return distributed


class OuterWrapper(ABC):

    def __init__(self, model_id, num_expected_inputs):
        """
        constructor for the outer wrapper, an abstract base class inherited by the inner wrapper
        :param model_id: the ID / unique name of the model, as defined in the inner wrapper
        :param num_expected_inputs: the number of unique types of input data messages the model needs in order to perform
                                an increment, as defined in the inner wrapper. Should equal the number of input schemas,
                                that is, the number of .json files in the model's schemas/input/ directory
        """

        self.model_id = model_id
        self.num_expected_inputs = num_expected_inputs
        self.status = 'booting'
        self.incstep = 1
        self.initial_year = -1
        self.increment_flag = False
        self.connected_to_broker = False

        self.pub_queue = Queue()
        self.broker_queue = Queue()
        self.action_queue = Queue()

        self.abstract_graph = Graph("/abstract-graph.geojson")
        self.instance_graph = Graph("/instance-graph.geojson")
        self.instance_graph.nodes['UnitedStates']['area'] = 8081900

        self.input_schemas = None
        self.output_schemas = None
        self.validated_schemas = {}
        self.initial_conditions = None
        self.generic_output_schema = '{' \
                                     '  "type": "object",' \
                                     '  "patternProperties": {' \
                                     '    ".*": {' \
                                     '      "type": "object", ' \
                                     '      "properties": {' \
                                     '         "data": {"type": "object"}, "granularity": {"type": "string"}' \
                                     '      },' \
                                     '      "required": ["data", "granularity"]' \
                                     '    }' \
                                     '  }' \
                                     '}'

        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                            format='%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s')

    def meet(self, a, b, graph=None):
        sort = sorted((a, b))
        return "{}^{}".format(sort[0], sort[1])

    def aggregate(self, data, src, dest, variable):
        if src == dest:
            return data
        path = nx.shortest_path(self.abstract_graph, dest, src)
        path.reverse()
        logging.info(path)
        if path:
            assert path[0] == src
            assert path[-1] == dest
            parents = defaultdict(list)
            for instance, value in data.items():
                if instance not in self.instance_graph.nodes:
                    logging.critical("instance {} not in instance graph".format(instance))
                    continue
                parent = [parent for parent in self.instance_graph.predecessors(instance) if self.instance_graph.nodes[parent]['type'] == path[1]]
                assert len(parent) == 1
                parents[parent[0]].append((instance, value))
            translated = {}
            for instance, values, in parents.items():
                trans_func_name = self.abstract_graph[path[1]][path[0]]['a'].get(variable)
                trans_func = self.instance_graph.functions.get(trans_func_name, self.instance_graph.default_aggregator)
                translated[instance] = trans_func([value[1] for value in values])
            return self.aggregate(translated, path[1], dest, variable)
        else:
            raise Exception("aggregation error")

    def disaggregate(self, data, src, dest, variable):
        if src == dest:
            return data
        path = nx.shortest_path(self.abstract_graph, src, dest)
        if path:
            assert path[0] == src
            assert path[-1] == dest
            translated = {}
            for instance, value in data.items():
                trans_func_name = self.abstract_graph[path[0]][path[1]]['d'].get(variable)
                trans_func = self.instance_graph.functions.get(trans_func_name, self.instance_graph.default_disaggregator)
                tmp = trans_func(value, instance, path[1])
                translated = {**translated, **tmp}
            return self.disaggregate(translated, path[1], dest, variable)
        else:
            raise Exception("disaggregation error")

    def translate(self, data, src, dest, variable):
        """

        :param data: dictionary mapping instances to their values
        :param src: granularity of the data (the abstract graph must have a node with the same name)
        :param dest: granularity to translate the data to (the abstract graph must have a node with the same name)
        :return: dictionary mapping new instances to their values
        """
        if src == dest:
            return data

        elif nx.has_path(self.abstract_graph, src, dest):
            return self.disaggregate(data, src, dest, variable)

        elif nx.has_path(self.abstract_graph, dest, src):
            return self.aggregate(data, src, dest, variable)

        elif nx.has_path(self.abstract_graph, src, self.meet(src, dest)) and nx.has_path(self.abstract_graph, dest, self.meet(src, dest)):
            disaggregated = self.disaggregate(data, src, self.meet(src, dest), variable)
            aggregated = self.aggregate(disaggregated, self.meet(src, dest), dest, variable)
            return aggregated

        else:
            logging.critical("error translating {} from {} to {}".format(variable, src, dest))
            raise Exception("error translating {} from {} to {}".format(variable, src, dest))

    def load_json_objects(self, dir_path):
        """
        load JSON objects from .json files
        :param dir_path: path to a directory with .json files
        :return: a dictionary that a maps a schema's filename (without the .json extension) to the corresponding JSON
                object / schema
        """

        schemas = {}
        for schema in glob.glob('{}/*.json'.format(dir_path)):
            with open(schema) as schema_file:
                file_name = os.path.splitext(os.path.basename(schema))[0]
                schemas[file_name] = json.load(schema_file)
        return schemas

    @abstractmethod
    def configure(self, **kwargs):
        """
        implemented in the inner wrapper. Initializes the model with its parameters, needed before any increments
        :param kwargs:
        :return:
        """

        raise NotImplementedError("configure() has to be implemented in the {} inner wrapper".format(self.model_id))

    @abstractmethod
    def increment(self, **kwargs):
        """
        implemented in the inner wrapper
        :param kwargs:
        :return:
        """

        raise NotImplementedError("increment() has to be implemented in the {} inner wrapper".format(self.model_id))

    def increment_handler(self, event, incstep):
        """
        Calls increment() after validating inputs, then validates the results of the increment
        :param event: the shutdown event for managing threads
        :param incstep: the increment number that is currently being performed, as understood by the broker
        :return: if the increment is successful, returns its results in a dictionary
        """

        self.increment_flag = True
        logging.info("about to increment, incstep {}, year {}".format(incstep, self.initial_year + incstep))
        self.incstep = incstep

        # validate against input schemas
        if incstep > 1 and len(self.validated_schemas) != self.num_expected_inputs:
            logging.critical("number of validated schemas {} != num_expected_inputs {}".format(len(self.validated_schemas), self.num_expected_inputs))
            event.set()
            raise RuntimeError

        # call the inner wrapper
        schemas = self.validated_schemas.copy()
        self.validated_schemas.clear()
        results, htmls, images = self.increment(**schemas)
        # translate results to the desired granularity?

        # validate against output schemas
        for schema_name, data_msg in results.items():
            try:
                validate(data_msg, json.loads(self.generic_output_schema))
                print(schema_name)
                print(data_msg)
                print(self.output_schemas)
                validate(data_msg, self.output_schemas[schema_name])
            except Exception as e:
                logging.critical("message {} failed to validate schema {}".format(data_msg, schema_name))
                event.set()
                raise RuntimeError

        if len(results) != len(self.output_schemas):
            logging.critical("didn't validate against every output schema")
            event.set()
            raise RuntimeError

        self.increment_flag = False
        for schema, data in results.items():
            data_msg = {}
            data_msg['schema'] = schema
            data_msg['payload'] = data
            data_msg['signal'] = 'data'
            data_msg['source'] = self.model_id
            data_msg['incstep'] = self.incstep
            data_msg['year'] = self.incstep + self.initial_year
            self.pub_queue.put(data_msg)
        for filename, html in htmls.items():
            file_msg = {}
            file_msg['name'] = filename
            file_msg['payload'] = html
            file_msg['signal'] = 'file_string'
            file_msg['source'] = self.model_id
            file_msg['incstep'] = self.incstep
            file_msg['year'] = self.incstep + self.initial_year
            self.pub_queue.put(file_msg)
        for filename, image in images.items():
            file_msg = {}
            file_msg['name'] = filename
            file_msg['payload'] = base64.b64encode(image)
            file_msg['signal'] = 'file_bytes'
            file_msg['source'] = self.model_id
            file_msg['incstep'] = self.incstep
            file_msg['year'] = self.incstep + self.initial_year
            self.pub_queue.put(file_msg)
        logging.info("finished increment {}, year {}".format(self.incstep, self.incstep + self.initial_year))
        self.incstep += 1

    def send_status(self, event):
        """
        creates a status message and puts it into the publish queue. A status message must include the model's ID,
        a signal / message type of "status", the increment step, and the current status:
            booting: model is waiting for the broker to boot (receive status messages from all models)
            waiting: model is waiting for its needed input data messages from other models
            ready: model can begin incrementing if it receives an increment pulse; it is at the first increment step,
                or it has received all input messages and has validated them against input schemas
            incrementing: model has received an increment pulse and is performing the increment in the handler
        :param event: the shutdown event for managing threads
        :return: runs continuously until the shutdown event is set
        """

        count = 0
        while not event.is_set():
            count += 1
            time.sleep(1)

            if self.connected_to_broker:
                if self.increment_flag:
                    # waiting for the increment to finish
                    self.status = 'incrementing'
                else:
                    if self.incstep == 1:
                        # kickstart the model for the first increment
                        self.status = 'ready'

                    elif len(self.validated_schemas) == self.num_expected_inputs:
                        # all input messages have been received and all input schemas have been validated
                        self.status = 'ready'

                    else:
                        # still waiting for messages from other models
                        self.status = 'waiting'
            else:
                self.status = 'booting'

            message = {}
            message['source'] = self.model_id
            message['id'] = count
            message['time'] = time.time()
            message['date'] = time.ctime()
            message['signal'] = 'status'
            message['incstep'] = self.incstep
            message['year'] = self.incstep + self.initial_year
            message['status'] = self.status
            self.pub_queue.put(message)

            logging.debug(json.dumps(message))

    def pub(self, event):
        """
        publishes messages to the broker, including status messages and data messages
        Sets the shutdown event if an outgoing data message matches more than one output schema.
        :param event: the shutdown event for managing threads
        :return: runs continuously until shutdown event is set, then closes its zmq socket
        """

        # connect to zmq
        context = zmq.Context()
        sock = context.socket(zmq.PUB)
        sock.setsockopt(zmq.LINGER, 1000)
        sock.connect('tcp://{}:{}'.format('broker', '5555'))

        while not event.is_set():

            # get message from the queue
            try:
                message = self.pub_queue.get(timeout=0.1)
            except Empty:
                continue

            # send status messages
            if message.get('signal') == 'status':
                sock.send_json(message)
                continue

            # send files
            if message.get('signal').startswith('file'):
                sock.send_json(message)
                continue

            # validate data messages
            matched = []
            for name, schema in self.output_schemas.items():
                try:
                    validate(message['payload'], schema)
                    logging.info("validated outgoing message: {}".format(message))
                    matched.append(schema)
                except ValidationError:
                    logging.info("validation error")
                except json.JSONDecodeError:
                    logging.warning("json decode error")
            if len(matched) == 0:
                logging.info("message didn't match any output schemas: {}".format(message))
            elif len(matched) == 1:
                logging.info("message matched an output schema: {}".format(message))
                sock.send_json(message)
            else:
                logging.critical("more than one output schema was matched: {}".format(message))
                event.set()

        sock.close()
        context.term()

    def sub(self, event):
        """
        connects to the broker's PUB as a subscriber and receives all messages sent from the broker,
        and all messages sent by other models and forwarded by the broker.
        Status messages from the broker go into the broker queue, for the watchdog.
        :param event: the shutdown event for managing threads
        :return: runs continuously until shutdown event is set, then closes its zmq socket
        """

        # connect to zmq
        context = zmq.Context()
        sock = context.socket(zmq.SUB)
        sock.setsockopt(zmq.SUBSCRIBE, b"")
        sock.setsockopt(zmq.RCVTIMEO, 0)
        sock.setsockopt(zmq.LINGER, 1000)
        sock.connect('tcp://{}:{}'.format('broker', '5556'))

        while not event.is_set():
            try:
                message = sock.recv_json()
            except zmq.ZMQError:
                continue
            logging.info(json.dumps(message))

            signal = message.get('signal')
            if signal == 'status' and message.get('source') == 'broker':
                self.broker_queue.put(message)
            elif signal == 'data':
                if not self.insert_data_message(message['payload']):
                    event.set()
            else:
                self.action_queue.put(message)

        sock.close()
        context.term()

    def insert_data_message(self, message):
        """
        validates a data message against the input schemas
        :param message: the payload of the data message to insert into the queue
        :return: False if message insertion throws an error, otherwise True.
                returns True if the message is validated by 0 or 1 schemas
                returns False if the data message is a duplicate
                (was validated by a schema already used since the last increment)
        """

        matched = []
        for name, schema in self.input_schemas.items():
            try:
                validate(message, schema)
                logging.info("schema {} validated incoming message: {}".format(name, message))
                if name in self.validated_schemas:
                    logging.error("schema {} already validated a message: {}".format(name, message))
                    return False
                else:
                    matched.append(schema)
                    self.validated_schemas[name] = message
            except ValidationError:
                logging.info("validation error")
            except json.JSONDecodeError:
                logging.warning("json decode error")

        if len(matched) == 0:
            logging.info("message didn't match any input schemas: {}".format(message))
        return True

    def action_worker(self, event):
        """
        move logic for parsing results and putting into pub_queue into self.increment_handler.
        gets messages from the action queue and performs the respective action. currently, just the increment action
        :param event: the shutdown event for managing threads
        :return: runs continuously until the shutdown event is set
        """

        while not event.is_set():
            try:
                message = self.action_queue.get(timeout=0.1)
            except Empty:
                continue

            if message['signal'] == 'increment':
                try:
                    self.increment_handler(event, message['incstep'])
                except Exception as e:
                    logging.critical(e)
                    event.set()
                    raise RuntimeError

    def watchdog(self, event):
        """
        verifies that the broker is running by receiving its status messages. Sets the connected_to_broker flag
        if the broker's status is booted, that is, if the broker has received status messages from all models,
        so that models can safely receive increment pulses and publish their data.
        Will set the shutdown event if a status message has not been received within the timeout interval
        :param event: the shutdown event for managing threads
        :return: runs continuously until the shutdown event is set
        """
        while not event.is_set():
            try:
                message = self.broker_queue.get(timeout=10)
                if message.get('status') == 'booted':
                    self.connected_to_broker = True
                    self.initial_year = message.get('initial_year')
            except Empty:
                logging.critical("Timed out waiting for broker message")
                event.set()

    def run(self):
        """
        main thread of the outer wrapper. Launches all sub threads. Called from the inner wrapper
        :return: runs continuously until shutdown event is set
        """

        # initialize the model
        self.input_schemas = self.load_json_objects('/opt/schemas/input')
        self.output_schemas = self.load_json_objects('/opt/schemas/output')
        self.initial_conditions = self.load_json_objects('/opt/config')
        self.configure(**self.initial_conditions)

        # start the threads
        shutdown = Event()

        subscribe_thread = Thread(target=self.sub, args=(shutdown,))
        subscribe_thread.start()

        publish_thread = Thread(target=self.pub, args=(shutdown,))
        publish_thread.start()

        action_thread = Thread(target=self.action_worker, args=(shutdown,))
        action_thread.start()

        watchdog_thread = Thread(target=self.watchdog, args=(shutdown,))
        watchdog_thread.start()

        status_thread = Thread(target=self.send_status, args=(shutdown,))
        status_thread.start()

        try:
            while not shutdown.is_set():
                time.sleep(1)
        except Exception as e:
            logging.critical(e)
        finally:
            shutdown.set()
            logging.critical("{} model has shut down".format(self.model_id))
