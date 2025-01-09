
"""
Simple decoder, accepts STIX input, outputs STIX entities
along with entity/context definitions for embedding.
"""

import urllib.parse
import json

from pulsar.schema import JsonSchema, Record, Bytes

from trustgraph.schema import topic, Error, Metadata, TextDocument
from trustgraph.schema import document_ingest_queue, text_ingest_queue
from trustgraph.base import ConsumerProducer
from trustgraph.schema import Triple, Triples, Metadata, Value
from trustgraph.schema import EntityContext, EntityContexts
from trustgraph.schema import triples_store_queue
from trustgraph.schema import entity_contexts_ingest_queue
from trustgraph.log_level import LogLevel
from trustgraph.base import ConsumerProducer
from trustgraph.knowledge import DESCRIPTION, IS_A, LABEL, KEYWORD
from trustgraph.knowledge import Uri, Literal
from trustgraph.rdf import TRUSTGRAPH_ENTITIES

# Local schema
from trustgraph_stix.schema import StixDocument, stix_ingest_queue

# Need the module name for consumer/producer registration, it's used as
# the default subscriber name
module = ".".join(__name__.split(".")[1:-1])

# Default queue settings
default_input_queue = stix_ingest_queue
default_output_queue = triples_store_queue
default_entity_context_queue = entity_contexts_ingest_queue
default_subscriber = module

# Makes URIs
def to_uri(text, prefix="stix"):

    part = text.replace(" ", "-").lower().encode("utf-8")
    quoted = urllib.parse.quote(part)
    uri = TRUSTGRAPH_ENTITIES + prefix + "/" + quoted

    return uri

IDENTITY_CLASS = to_uri("identity", "stix-rel")

# This processor is defined as a class subclassed from ConsumerProducer,
# which means it consumes data, processes it, and then can forward on
# as a producer.
class Processor(ConsumerProducer):

    def __init__(self, **params):

        # Ingest config (using default settings)
        input_queue = params.get("input_queue", default_input_queue)
        output_queue = params.get("output_queue", default_output_queue)
        ec_queue = params.get(
            "entity_context_queue",
            default_entity_context_queue
        )
        subscriber = params.get("subscriber", default_subscriber)

        # Initialise parent class, takes care of Pulsar configuration
        super(Processor, self).__init__(
            **params | {
                "input_queue": input_queue,
                "output_queue": output_queue,
                "subscriber": subscriber,
                "input_schema": StixDocument,
                "output_schema": Triples,
                "vector_schema": EntityContexts.__name__,
            }
        )

        # The producer side has an extra output for entity contexts.
        self.ec_prod = self.client.create_producer(
            topic=ec_queue,
            schema=JsonSchema(EntityContexts),
        )

        # The ConsumerProducer class sets up a Prometheus metric with
        # default information in it, this sets its value again to include
        # information about the entity context queue and schema
        __class__.pubsub_metric.info({
            "input_queue": input_queue,
            "output_queue": output_queue,
            "entity_context_queue": ec_queue,
            "subscriber": subscriber,
            "input_schema": StixDocument.__name__,
            "output_schema": Triples.__name__,
            "vector_schema": EntityContexts.__name__,
        })

    # Unpack a STIX document, returns triples and entity context array
    def unpack(self, stix):

        # Get STIX document ID
        id = Uri(to_uri(stix["id"], "bundle"))

        # Gonna build up two lists
        triples = []
        entities = []

        for object in stix["objects"]:

            # Ignore objects with mandatory stuff missing
            if "id" not in object:
                print("STIX object without id", flush=True)
                continue

            if "type" not in object:
                print("STIX object without type", flush=True)
                continue

            # Get object type
            type = object["type"]

            # Convert type into URI
            type_uri = Uri(to_uri(type, "type"))

            # Get object ID and type
            oid = object["id"]
            oid_uri = Uri(to_uri(object["id"], type))

            # Add type property for the object, and make sure the type
            # itself has a label
            triples.extend([
                (oid_uri, Uri(IS_A), type_uri),
                (type_uri, Uri(LABEL), type)
            ])

            # If the object has a description, add as an entity property
            # and also use the definition in an entity context which gets
            # mapped to a graph embedding
            if "description" in object:
                triples.append(
                    (oid_uri, Uri(DESCRIPTION), Literal(object["description"]))
                )
                entities.append(
                    (oid_uri, object["description"])
                )

            # If the object has a name, add as a label property
            # and also use the definition in an entity context which gets
            # mapped to a graph embedding
            if "name" in object:
                triples.append(
                    (oid_uri, Uri(LABEL), Literal(object["name"]))
                )
                entities.append(
                    (oid_uri, object["name"])
                )

            # Add labels as keyword properties
            if "labels" in object:
                for label in object["labels"]:
                    triples.append(
                        (oid_uri, Uri(KEYWORD), Literal(label))
                    )

            # Add identity_class as a property, and make sure the
            # identity_class has a label.
            if "identity" in object:
                if "identity_class" in object:

                    ident_class_uri = Uri(
                        to_uri(object["identity_class"], "id-class")
                    )

                    triples.extend([
                        (oid_uri, Uri(IDENTITY_CLASS), ident_class_uri),
                        (ident_uri, Uri(LABEL), object["identity_class"]),
                    ])

            # identity_class label and type label probably get written
            # many times, but that's OK.  Semantics of writing triples is
            # that it's a No-op if the triple already exists

        # Convert into Pulsar objects
        triples = [
            Triple(
                s = Value(value=t[0], is_uri=isinstance(t[0], Uri)),
                p = Value(value=t[1], is_uri=isinstance(t[1], Uri)),
                o = Value(value=t[2], is_uri=isinstance(t[2], Uri)),
            )
            for t in triples
        ]

        # Convert into Pulsar objects
        entities = [
            EntityContext(
                entity = Value(value=e[0], is_uri=isinstance(e[0], Uri)),
                context = e[1]
            )
            for e in entities
        ]

        return triples, entities

    # Called to handle next event on the queue
    def handle(self, msg):

        try:

            v = msg.value()
            print(f"Processing {v.metadata.id}...", flush=True)

            # This payload was created by cyber_extract, it was encoded as
            # UTF-8
            stix = v.stix.decode("utf-8")

            # JSON-parse the STIX blob
            print("Unpacking...")
            object = json.loads(stix)

            # Unpack to triples and entity contexts
            triples, entities = self.unpack(object)

            print("Forward response...")

            # Forward triple and entity context objects
            t = Triples(
                metadata=v.metadata,
                triples=triples,
            )
            self.producer.send(t)

            t = EntityContexts(
                metadata=v.metadata,
                entities=entities,
            )
            self.ec_prod.send(t)

        except Exception as e:
            print("Exception: ", e, flush=True)

        print("Done.", flush=True)

    @staticmethod
    def add_args(parser):

        # This configures the standard set of command-line arguments
        # which are provided by ConsumerProducer
        ConsumerProducer.add_args(
            parser, default_input_queue, default_subscriber,
            default_output_queue,
        )

        # Also add an argument for the entity-context queue
        parser.add_argument(
            '-e', '--entity-context-queue',
            default=default_entity_context_queue,
            help=f'Entity context queue (default: {default_entity_context_queue})'
        )

def run():

    Processor.start(module, __doc__)

