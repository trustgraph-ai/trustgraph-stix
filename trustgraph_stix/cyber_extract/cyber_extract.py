
"""
Simple decoder, accepts text documents on input, outputs extracted STIX 2
data as a JSON-encoded STIX package of extracted objects.
"""

import json
import uuid

from trustgraph.schema import topic, Error, Metadata, TextDocument
from trustgraph.schema import document_ingest_queue, text_ingest_queue
from trustgraph.schema import prompt_request_queue, prompt_response_queue
from trustgraph.base import ConsumerProducer
from trustgraph.clients.prompt_client import PromptClient

# Local schema
from trustgraph_stix.schema import StixDocument, stix_ingest_queue

# Need the module name for consumer/producer registration, it's used as
# the default subscriber name
module = ".".join(__name__.split(".")[1:-1])

# Default queue settings
default_input_queue = text_ingest_queue
default_output_queue = stix_ingest_queue
default_subscriber = module

# This processor is defined as a class subclassed from ConsumerProducer,
# which means it consumes data, processes it, and then can forward on
# as a producer.
class Processor(ConsumerProducer):

    # Constructor
    def __init__(self, **params):

        # Ingest config (using default settings)
        input_queue = params.get("input_queue", default_input_queue)
        output_queue = params.get("output_queue", default_output_queue)
        subscriber = params.get("subscriber", default_subscriber)
        pr_request_queue = params.get(
            "prompt_request_queue", prompt_request_queue
        )
        pr_response_queue = params.get(
            "prompt_response_queue", prompt_response_queue
        )

        # Initialise parent class, takes care of Pulsar configuration
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

        # Set up the prompt client
        self.prompt = PromptClient(
            pulsar_host=self.pulsar_host,
            input_queue=pr_request_queue,
            output_queue=pr_response_queue,
            subscriber = subscriber + "-prompt",
        )

        print("Initialised")

    # Method, takes a bunch of text and uses the LLM to extract STIX
    # objects
    def extract_stix(self, text):

        # Use the prompt client to extract STIX SDO
        sdo = self.prompt.request(
            "stix-sdo",
            {
                "text": text
            }
        )

        # Encode as JSON
        enc_sdo = json.dumps(sdo, indent=4)

        print("Got SDO")

        # Use the prompt client to extract STIX SCO
        sco = self.prompt.request(
            "stix-sco",
            {
                "text": text
            }
        )

        print("Got SCO")

        # Encode as JSON
        enc_sco = json.dumps(sco, indent=4)

        # Form a request which takes the SCO and SDO output as input
        sro = self.prompt.request(
            "stix-sro",
            {
                "text": text,
                "stix_sdo": enc_sdo,
                "stix_sco": enc_sco,
            }
        )

        print("Got SRO")

        # Turn the whole lot into a STIX bundle with generated ID
        pkg = {
            "type": "bundle",
            "id": f"bundle--{uuid.uuid4()}",
            "objects": sdo + sco + sro
        }        

        return pkg

    # Called to handle next event on the queue
    def handle(self, msg):

        print("Text doc received", flush=True)

        v = msg.value()

        print(f"Decoding {v.metadata.id}...", flush=True)

        # FIXME: Make charset a parameter?
        text = v.text.decode("utf-8")

        # Turn text into STIX
        pkg = self.extract_stix(text)

        print("STIX extraction successful", flush=True)

        # Encode as JSON
        enc = json.dumps(pkg)

        # Create a Pulsar message and send to next queue
        r = StixDocument(
            metadata=v.metadata,
            stix=enc.encode("utf-8"),
        )
        self.send(r)

        print("Done.", flush=True)

    @staticmethod
    def add_args(parser):

        # This configures the standard set of command-line arguments
        # which are provided by ConsumerProducer, we don't need any others
        ConsumerProducer.add_args(
            parser, default_input_queue, default_subscriber,
            default_output_queue,
        )

def run():

    Processor.start(module, __doc__)

