
"""
Simple decoder, accepts text documents on input, outputs extracted STIX
data as a STIX package of extracted objects.
"""

import tempfile
import json
import uuid

from pulsar.schema import Record, Bytes

from trustgraph.schema import topic, Error, Metadata, TextDocument
from trustgraph.schema import document_ingest_queue, text_ingest_queue
from trustgraph.schema import prompt_request_queue, prompt_response_queue
from trustgraph.base import ConsumerProducer
from trustgraph.clients.prompt_client import PromptClient

module = ".".join(__name__.split(".")[1:-1])

stix_ingest_queue = topic('stix-load')

default_input_queue = text_ingest_queue
default_output_queue = stix_ingest_queue
default_subscriber = module

class StixDocument(Record):
    metadata = Metadata()
    stix = Bytes()

class Processor(ConsumerProducer):

    def __init__(self, **params):

        input_queue = params.get("input_queue", default_input_queue)
        output_queue = params.get("output_queue", default_output_queue)
        subscriber = params.get("subscriber", default_subscriber)
        pr_request_queue = params.get(
            "prompt_request_queue", prompt_request_queue
        )
        pr_response_queue = params.get(
            "prompt_response_queue", prompt_response_queue
        )

        super(Processor, self).__init__(
            **params | {
                "input_queue": input_queue,
                "output_queue": output_queue,
                "subscriber": subscriber,
                "input_schema": TextDocument,
                "output_schema": StixDocument,
                "prompt_request_queue": pr_request_queue,
                "prompt_response_queue": pr_response_queue,
            }
        )

        self.prompt = PromptClient(
            pulsar_host=self.pulsar_host,
            input_queue=pr_request_queue,
            output_queue=pr_response_queue,
            subscriber = subscriber + "-prompt",
        )

        print("Initialised")

    def extract_stix(self, text):

        sdo = self.prompt.request(
            "stix-sdo",
            {
                "text": text
            }
        )

        print("Got SDO")

        enc_sdo = json.dumps(sdo, indent=4)

#        print("====SDO")
#        print(stix_sdo)

        sco = self.prompt.request(
            "stix-sco",
            {
                "text": text
            }
        )

        print("Got SCO")


        enc_sco = json.dumps(sco, indent=4)

#        print("====SCO")
#        print(stix_sco)

        sro = self.prompt.request(
            "stix-sro",
            {
                "text": text,
                "stix_sdo": enc_sdo,
                "stix_sco": enc_sco,
            }
        )

#        stix_sro = json.dumps(sro, indent=4)
#        print("====SRO")
#        print(stix_sro)

        pkg = {
            "type": "bundle",
            "id": f"bundle--{uuid.uuid4()}",
            "objects": sdo + sco + sro
        }        

        print("=====")
        print(pkg)

        return pkg

    def handle(self, msg):

        print("Text doc received", flush=True)

        v = msg.value()

        print(f"Decoding {v.metadata.id}...", flush=True)

        # FIXME: Make charset a parameter?
        text = v.text.decode("utf-8")

        pkg = self.extract_stix(text)

        print("STIX extraction successful", flush=True)

        enc = json.dumps(pkg)

        r = StixDocument(
            metadata=v.metadata,
            stix=enc.encode("utf-8"),
        )

        self.send(r)

        print("Done.", flush=True)

    @staticmethod
    def add_args(parser):

        ConsumerProducer.add_args(
            parser, default_input_queue, default_subscriber,
            default_output_queue,
        )

def run():

    Processor.start(module, __doc__)

