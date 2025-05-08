
"""
Simple decoder, accepts text documents on input, outputs extracted STIX 2
data as a JSON-encoded STIX package of extracted objects.
"""

import json
import uuid

from trustgraph.schema import TextDocument

from trustgraph.base import FlowProcessor, ConsumerSpec, ProducerSpec
from trustgraph.base import PromptClientSpec

# Every processor has an ID which it uses to get its configuration
# information.  The ID can be overriden
default_ident = "cyber-extract"

# Local schema
from trustgraph_stix.schema import StixDocument

# This processor is defined as a class subclassed from FlowProcess,
# which supports managing queue resources
class Processor(FlowProcessor):

    # Constructor
    def __init__(self, **params):

        # Get the ID
        id = params.get("id", default_ident)

        # Initialise parent class, takes care of Pulsar configuration
        super(Processor, self).__init__(
            **params | {
                "id": id,
            }
        )

        # The rest of this configures connections.  TrustGraph processing
        # organises data into separate 'flows' which are logically
        # separate.  Each flow has its own Pulsar queues, even if data
        # is going through the same processors and processing functions.
        # When flows are set up, queeus are configured automatically as
        # defined by the specifications here.

        # The names for producers and consumers is used to look up the
        # queue names in the flowclass specification.

        # Configure input
        self.register_specification(
            ConsumerSpec(
                name = "input",             # Identifier, as used in the
                                            # flow class definition
                schema = TextDocument,      # Schema
                handler = self.on_message,  # Handler to call on each message
            )
        )

        # Configure connection to the prompt service.  This sets up a
        # consumer and producer to make a round-trip request to the
        # prompt service
        self.register_specification(
            PromptClientSpec(
                request_name = "prompt-request",   # Identifier, as used in
                                                   # the flow class
                response_name = "prompt-response", # Response identifier
            )
        )

        # Configure output connection
        self.register_specification(
            ProducerSpec(
                name = "output",        # Identifier, as used in the
                                        # flow class definition
                schema = StixDocument,  # Schema
            )
        )

        print("Initialised")

    # Method, takes a bunch of text and uses the LLM to extract STIX
    # objects
    async def extract_stix(self, text, prompt):

        sdo = await prompt(
            id = "stix-sdo",
            variables = {
                "text": text
            }
        )

        # Encode as JSON
        enc_sdo = json.dumps(sdo, indent=4)

        print("Got SDO")

        # Use the prompt client to extract STIX SCO
        sco = await prompt(
            id = "stix-sco",
            variables = {
                "text": text
            }
        )

        print("Got SCO")

        # Encode as JSON
        enc_sco = json.dumps(sco, indent=4)

        # Form a request which takes the SCO and SDO output as input
        sro = await prompt(
            id = "stix-sro",
            variables = {
                "text": text,
                "stix_sdo": enc_sdo,
                "stix_sco": enc_sco
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
    async def on_message(self, msg, consumer, flow):

        print("Text doc received", flush=True)

        # Input is a Pulsar message, this gets the contents
        v = msg.value()

        print(f"Decoding {v.metadata.id}...", flush=True)

        # FIXME: Make charset a parameter?
        text = v.text.decode("utf-8")

        # Turn text into STIX
        pkg = await self.extract_stix(text, flow("prompt-request").prompt)

        print("STIX extraction successful", flush=True)

        # Encode as JSON
        enc = json.dumps(pkg)

        # Create a Pulsar message and send to next queue
        r = StixDocument(
            metadata = v.metadata,
            stix = enc.encode("utf-8"),
        )

        # Send to the next processor
        await flow("output").send(r)

        print("Done.", flush=True)

    @staticmethod
    def add_args(parser):

        # This configures the standard set of command-line arguments
        # which are provided by ConsumerProducer, we don't need any others
        FlowProcessor.add_args(parser)

def run():

    Processor.launch(default_ident, __doc__)

