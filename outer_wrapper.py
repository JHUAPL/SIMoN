# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the MIT License.


import zmq
import json
from jsonschema import validate, ValidationError
import time
import glob
from threading import Thread, Event
from queue import Queue, Empty
from abc import ABC, abstractmethod
import os
import sys
import logging
import networkx as nx
from collections import defaultdict


class Graph(nx.DiGraph):
    def __init__(self, filename):
        """
        constructor for the granularity graph
        builds a graph by loading it from a JSON file
        :param filename: path to the JSON file
        """

        # call the networkx parent constructor
        super().__init__()

        # map the translation function names to the functions
        self.functions = {
            "simple_sum": self.simple_sum,
            "simple_average": self.simple_average,
            "weighted_average": self.weighted_average,
            "distribute_uniformly": self.distribute_uniformly,
            "distribute_by_area": self.distribute_by_area,
            "distribute_identically": self.distribute_identically,
        }

        # build the graph by loading it from the JSON file
        with open(filename, mode='r') as json_file:
            data = json.load(json_file)
        for node in data['nodes']:
            self.add_node(
                node['id'],
                name=node.get('name'),
                type=node.get('type'),
                shape=node.get('shape'),
                area=node.get('area'),
            )
        for edge in data['links']:
            self.add_edge(edge['source'], edge['target'])

    def simple_sum(self, values, *args):
        """
        aggregator for an instance graph
        :param values: a list of value tuples: (instance node name, node value)
        :return: the sum of the values
        """
        return sum([value[1] for value in values])

    def simple_average(self, values, *args):
        """
        aggregator for an instance graph
        :param values: a list of value tuples: (instance node name, node value)
        :return: the mean of the values
        """
        return sum([value[1] for value in values]) / len(values)

    def weighted_average(self, values, parent_granularity, *args):
        """
        aggregator for an instance graph
        :param values: a list of value tuples: (instance node name, node value)
        :return: the area-weighted mean of the values
        """

        # get the parents of the first node (each node should have the same parents)
        ancestors = nx.ancestors(self, values[0][0])

        # get the area of the parent instance node
        for ancestor in ancestors:
            if self.nodes[ancestor]['type'] == parent_granularity:
                parent_area = self.nodes[ancestor]['area']
                break
        else:
            logging.error(
                f"none of the nodes in {ancestors} have granularity {parent_granularity}"
            )
            parent_area = sum(
                [self.nodes[value[0]]['area'] for value in values]
            )

        return (
            sum([value[1] * self.nodes[value[0]]['area'] for value in values])
            / parent_area
        )

    def distribute_uniformly(self, value, instance, child_granularity):
        """
        disaggregator for an instance graph
        :param value: the value of the parent node
        :param instance: the parent node to disaggregate
        :param child_granularity: the intended granularity of the transformation (the child node of the instance in the abstract graph)
        :return: a dict mapping each child node to its equal share of the parent value
        """
        children = [
            child
            for child in self.successors(instance)
            if self.nodes[child]['type'] == child_granularity
        ]
        mean = value / len(children) if children else 0
        distributed = {child: mean for child in children}
        return distributed

    def distribute_identically(self, value, instance, child_granularity):
        """
        disaggregator for an instance graph
        :param value: the value of the parent node
        :param instance: the parent node to disaggregate
        :param child_granularity: the intended granularity of the transformation (the child node of the instance in the abstract graph)
        :return: a dict mapping each child node to the parent value
        """
        children = [
            child
            for child in self.successors(instance)
            if self.nodes[child]['type'] == child_granularity
        ]
        distributed = {child: value for child in children}
        return distributed

    def distribute_by_area(self, value, instance, child_granularity):
        """
        disaggregator for an instance graph
        :param value: the value of the parent node
        :param instance: the parent node to disaggregate
        :param child_granularity: the intended granularity of the transformation (the child node of the instance in the abstract graph)
        :return: a dict mapping ecah child node to its area-proportionate share of the parent value
        """
        children = [
            child
            for child in self.successors(instance)
            if self.nodes[child]['type'] == child_granularity
        ]
        parent_area = self.nodes[instance]["area"]
        distributed = {
            child: value * self.nodes[child]["area"] / parent_area
            for child in children
        }
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
        self.default_agg = "simple_sum"
        self.default_dagg = "distribute_by_area"

        self.input_schemas = None
        self.output_schemas = None
        self.validated_schemas = {}
        self.generic_output_schema = (
            '{'
            '  "type": "object",'
            '  "patternProperties": {'
            '    ".*": {'
            '      "type": "object", '
            '      "properties": {'
            '         "data": {"type": "object"}, "granularity": {"type": "string"}'
            '      },'
            '      "required": ["data", "granularity"]'
            '    }'
            '  }'
            '}'
        )

        logging.basicConfig(
            level=logging.DEBUG,
            stream=sys.stdout,
            format='%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s',
        )

    def meet(self, a, b):
        sort = sorted((a, b))
        return f"{sort[0]}^{sort[1]}"

    def aggregate(self, data, src, dest, agg_name=None):

        if not agg_name:
            agg_name = self.default_agg

        # no translation needed
        if src == dest:
            return data

        # get path across the granularity graph
        path = nx.shortest_path(self.abstract_graph, dest, src)
        path.reverse()
        if path:
            assert path[0] == src
            assert path[-1] == dest

            # group the instances by their parent
            parents = defaultdict(list)
            for instance, value in data.items():
                if instance not in self.instance_graph.nodes:
                    logging.warning(
                        f"instance {instance} not in instance graph"
                    )
                    continue
                parent = [
                    parent
                    for parent in self.instance_graph.predecessors(instance)
                    if self.instance_graph.nodes[parent]['type'] == path[1]
                ]
                assert len(parent) == 1
                parents[parent[0]].append((instance, value))

            # aggregate each parent's child values
            translated = {}
            for instance, values in parents.items():
                trans_func = self.instance_graph.functions.get(agg_name)
                translated[instance] = trans_func(values)

            # translate to the next granularity in the path
            return self.aggregate(translated, path[1], dest, agg_name)
        else:
            raise Exception(
                f"error aggregating from {src} to {dest}, no path found"
            )

    def disaggregate(self, data, src, dest, disagg_name=None):

        if not disagg_name:
            disagg_name = self.default_dagg

        # no translation needed
        if src == dest:
            return data

        # get path across the granularity graph
        path = nx.shortest_path(self.abstract_graph, src, dest)
        if path:
            assert path[0] == src
            assert path[-1] == dest

            # iterate over each parent instance
            translated = {}
            for instance, value in data.items():
                if instance not in self.instance_graph.nodes:
                    logging.warning(
                        f"instance {instance} not in instance graph"
                    )
                else:
                    trans_func = self.instance_graph.functions.get(disagg_name)
                    # for this parent, create a dict of child instances mapped to disaggregated values
                    children = trans_func(value, instance, path[1])
                    # add this parent's dict of children to the flat dict
                    translated = {**translated, **children}

            # translate to the next granularity in the path
            return self.disaggregate(translated, path[1], dest, disagg_name)
        else:
            raise Exception(
                f"error disaggregating from {src} to {dest}, no path found"
            )

    def translate(
        self, data, src, dest, variable, agg_name=None, disagg_name=None
    ):
        """

        :param data: dictionary mapping instance nodes (of src granularity) to their values
        :param src: granularity of the data (the abstract graph must have a node with the same name)
        :param dest: granularity to translate the data to (the abstract graph must have a node with the same name)
        :return: dictionary mapping instance nodes (of dest granularity) to their values
        """

        # default aggregator and disaggregator
        if not agg_name:
            agg_name = self.default_agg
        if not disagg_name:
            disagg_name = self.default_dagg

        # no translation necessary
        if src == dest:
            return data

        # disaggregate straight down a branch of the granularity graph
        elif nx.has_path(self.abstract_graph, src, dest):
            return self.disaggregate(data, src, dest, disagg_name)

        # aggregate straight up a branch of the granularity graph
        elif nx.has_path(self.abstract_graph, dest, src):
            return self.aggregate(data, src, dest, agg_name)

        # translate between branches of the granularity graph: disaggregate down, then aggregate back up
        elif nx.has_path(
            self.abstract_graph, src, self.meet(src, dest)
        ) and nx.has_path(self.abstract_graph, dest, self.meet(src, dest)):
            disaggregated = self.disaggregate(
                data, src, self.meet(src, dest), disagg_name
            )
            aggregated = self.aggregate(
                disaggregated, self.meet(src, dest), dest, agg_name
            )
            return aggregated

        else:
            raise Exception(
                f"error translating {variable} from {src} to {dest}, no path found"
            )

    def load_json_objects(self, dir_path):
        """
        load JSON objects from .json files
        :param dir_path: path to a directory with .json files
        :return: a dictionary that a maps a schema's filename (without the .json extension) to the corresponding JSON
                object / schema
        """

        schemas = {}
        for schema in glob.glob(f'{dir_path}/*.json'):
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

        raise NotImplementedError(
            f"configure() has to be implemented in the {self.model_id} inner wrapper"
        )

    @abstractmethod
    def increment(self, **kwargs):
        """
        implemented in the inner wrapper
        :param kwargs:
        :return:
        """

        raise NotImplementedError(
            f"increment() has to be implemented in the {self.model_id} inner wrapper"
        )

    def increment_handler(self, event, incstep):
        """
        Calls increment() after validating inputs, then validates the results of the increment
        :param event: the shutdown event for managing threads
        :param incstep: the increment number that is currently being performed, as understood by the broker
        :return: if the increment is successful, returns its results in a dictionary
        """

        self.increment_flag = True
        logging.info(
            f"about to increment, incstep {incstep}, year {self.initial_year + incstep}"
        )
        self.incstep = incstep

        # validate against input schemas
        if (
            incstep > 1
            and len(self.validated_schemas) != self.num_expected_inputs
        ):
            logging.critical(
                f"number of validated schemas {len(self.validated_schemas)} != num_expected_inputs {self.num_expected_inputs}"
            )
            event.set()
            raise RuntimeError

        # call the inner wrapper
        schemas = self.validated_schemas.copy()
        self.validated_schemas.clear()
        results = self.increment(**schemas)

        # validate against output schemas
        for schema_name, data_msg in results.items():
            try:
                validate(data_msg, json.loads(self.generic_output_schema))
                validate(data_msg, self.output_schemas[schema_name])
            except Exception as e:
                logging.critical(
                    f"message {data_msg} failed to validate schema {schema_name}"
                )
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
        logging.info(
            f"finished increment {self.incstep}, year {self.incstep + self.initial_year}"
        )
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

                    elif (
                        len(self.validated_schemas) == self.num_expected_inputs
                    ):
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

    def pub(self, event, context):
        """
        publishes messages to the broker, including status messages and data messages
        Sets the shutdown event if an outgoing data message matches more than one output schema.
        :param event: the shutdown event for managing threads
        :return: runs continuously until shutdown event is set, then closes its zmq socket
        """

        # connect to zmq
        sock = context.socket(zmq.PUB)
        sock.setsockopt(zmq.LINGER, 1000)
        sock.connect('tcp://broker:5555')

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

            # validate data messages
            matched = []
            for name, schema in self.output_schemas.items():
                try:
                    validate(message['payload'], schema)
                    logging.info(f"validated outgoing message: {message}")
                    matched.append(schema)

                    # translate each data variable to output schema's granularity
                    for item in message['payload']:

                        # get current granularity from the data message
                        src_gran = message['payload'][item]['granularity']

                        # get granularity and translation functions from the schema
                        dest_gran = schema['properties'][item]['properties'][
                            'granularity'
                        ].get('value', src_gran)
                        agg = (
                            schema['properties'][item]['properties']
                            .get('agg', {})
                            .get('value')
                        )
                        dagg = (
                            schema['properties'][item]['properties']
                            .get('dagg', {})
                            .get('value')
                        )

                        # translate the data and update the data message
                        logging.info(
                            f"validating output: message from {name}, translating variable {item}, {src_gran} -> {dest_gran}"
                        )
                        data = self.translate(
                            message['payload'][item]['data'],
                            src_gran,
                            dest_gran,
                            item,
                            agg_name=agg,
                            disagg_name=dagg,
                        )
                        message['payload'][item]['data'] = data
                        message['payload'][item]['granularity'] = dest_gran

                except ValidationError:
                    logging.info("validation error")
                except json.JSONDecodeError:
                    logging.warning("json decode error")
            if len(matched) == 0:
                logging.info(
                    f"message didn't match any output schemas: {message['source']}"
                )
            elif len(matched) == 1:
                logging.info(
                    f"message matched an output schema: {message['source']}"
                )
                sock.send_json(message)
            else:
                logging.critical(
                    f"more than one output schema was matched: {message['source']}"
                )
                event.set()

        sock.close()

    def sub(self, event, context):
        """
        connects to the broker's PUB as a subscriber and receives all messages sent from the broker,
        and all messages sent by other models and forwarded by the broker.
        Status messages from the broker go into the broker queue, for the watchdog.
        :param event: the shutdown event for managing threads
        :return: runs continuously until shutdown event is set, then closes its zmq socket
        """

        # connect to zmq
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

            signal = message.get('signal')
            if signal == 'status' and message.get('source') == 'broker':
                self.broker_queue.put(message)
            elif signal == 'data':
                if not self.insert_data_message(message):
                    event.set()
            else:
                self.action_queue.put(message)

        sock.close()

    def insert_data_message(self, message):
        """
        validates a data message against the input schemas
        :param message: the data message to insert into the queue
        :return: False if message insertion throws an error, otherwise True.
                returns True if the message is validated by 0 or 1 schemas
                returns False if the data message is a duplicate
                (was validated by a schema already used since the last increment)
        """

        # validate data messages
        matched = []
        for name, schema in self.input_schemas.items():
            try:
                validate(message['payload'], schema)
                logging.info(
                    f"schema {name} validated incoming message: {message}"
                )
                if name in self.validated_schemas:
                    logging.error(
                        f"schema {name} already validated a message: {message}"
                    )
                    return False
                else:
                    matched.append(schema)

                    # translate each data variable to input schema's granularity
                    for item in message['payload']:

                        # get current granularity from the data message
                        src_gran = message['payload'][item]['granularity']

                        # get granularity and translation functions from the schema
                        dest_gran = schema['properties'][item]['properties'][
                            'granularity'
                        ].get('value', src_gran)
                        agg = (
                            schema['properties'][item]['properties']
                            .get('agg', {})
                            .get('value')
                        )
                        dagg = (
                            schema['properties'][item]['properties']
                            .get('dagg', {})
                            .get('value')
                        )

                        # translate the data and update the data message
                        logging.info(
                            f"validating input: message from {name}, translating variable {item}, {src_gran} -> {dest_gran}"
                        )
                        data = self.translate(
                            message['payload'][item]['data'],
                            src_gran,
                            dest_gran,
                            item,
                            agg_name=agg,
                            disagg_name=dagg,
                        )
                        message['payload'][item]['data'] = data
                        message['payload'][item]['granularity'] = dest_gran

                    self.validated_schemas[name] = message['payload']
            except ValidationError:
                logging.info("validation error")
            except json.JSONDecodeError:
                logging.warning("json decode error")

        if len(matched) == 0:
            logging.info(
                f"message didn't match any input schemas: {message['source']}"
            )
        return True

    def action_worker(self, event):
        """
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
        initial_conditions = self.load_json_objects('/opt/config')
        self.configure(**initial_conditions)

        # start the threads
        shutdown = Event()
        context = zmq.Context()

        # listen for messages
        subscribe_thread = Thread(target=self.sub, args=(shutdown, context,))
        subscribe_thread.start()

        # publish messages
        publish_thread = Thread(target=self.pub, args=(shutdown, context,))
        publish_thread.start()

        # handle increments
        action_thread = Thread(target=self.action_worker, args=(shutdown,))
        action_thread.start()

        # check connectivity to broker
        watchdog_thread = Thread(target=self.watchdog, args=(shutdown,))
        watchdog_thread.start()

        # submit updated status to the publish queue
        status_thread = Thread(target=self.send_status, args=(shutdown,))
        status_thread.start()

        try:
            while not shutdown.is_set():
                time.sleep(1)
        except Exception as e:
            logging.critical(e)
        finally:
            context.term()
            shutdown.set()
            logging.critical(f"{self.model_id} model has shut down")
