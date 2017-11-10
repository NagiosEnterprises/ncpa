
from __future__ import with_statement

import logging
import nagioshandler
from kafka import KafkaProducer
from kafka.errors import KafkaError
import listener.server
import json


class KafkaTopicItem:
    def __init__(self):
        self.check_time = 0
        self.hostname = ""
        self.servicename = ""
        self.check_type = ""
        self.state = -1
        self.output = ""


class Handler(nagioshandler.NagiosHandler):
    """
    Class for handling the passive KAFKA component.
    """
    def __init__(self, config, *args, **kwargs):
        super(Handler, self).__init__(config, *args, **kwargs)
        listener.server.listener.config['iconfig'] = config
        self.str_topic = self.config.get('kafkaproducer', 'topic')
        self.str_kafakhosts = self.config.get('kafkaproducer', 'servers')
        self.str_client_id = self.config.get('kafkaproducer', 'clientname')


    @staticmethod
    def do_check(check):
        stdout, returncode = check.run()
        if stdout is None or returncode is None:
            logging.error("Error running check for %s|%s given the instruction: %s, skipping.",
                          check.hostname,
                          check.servicename,
                          check.instruction)
        if check.servicename == '__HOST__':
            check_type = 'host'
        else:
            check_type = 'service'
        item = KafkaTopicItem()
        item.hostname = unicode(check.hostname)
        item.state = unicode(returncode)
        item.output = unicode(stdout)
        item.check_type = check_type
        if not check_type == 'host':
            item.servicename = check.servicename;
        return item

    def get_kafka_hostname(self, item):
        try:
            kafka_hostname = self.config.get('kafkaproducer', 'hostname', None)
            if kafka_hostname != 'None':
                return kafka_hostname
        except :
            pass
        return item.hostname

    @staticmethod
    def format_for_kafka(self, item):
        data = {
            'hostname': item.hostname,
            'servicename': item.servicename,
            'check_type': item.check_type,
            'check_time': item.check_time,
            'state': item.state,
            'output': item.output
        }
        return data

    def run(self, run_time):
        """
        Send checkresults to Kafka Topic
        """
        logging.debug("Establishing passive handler: Kafka")
        super(Handler, self).run()
        itemlist = []
        for check in self.checks:
            if check.needs_to_run():
                item = self.do_check(check)
                item.check_time = run_time
                check.set_next_run(run_time)
                item.hostname = self.get_kafka_hostname(item)
                itemlist.append(item)

        if len(itemlist) > 0:
            try:
                logging.info('Connect to Kafka Server')
                producer = KafkaProducer(bootstrap_servers=['{}'.format(self.str_kafakhosts)], client_id=self.str_client_id)
            except KafkaError:
                logging.warn(
                    'Problem to connect Kafka Server: {} with Topic: {} and Clientname {} '.format(self.str_kafakhosts,
                                                                                                   self.str_topic,
                                                                                                   self.str_client_id))
            for item in itemlist:
                producer.send(self.str_topic, key=str(item.hostname), value=json.dumps(self.format_for_kafka(self, item)))

            producer.flush()
