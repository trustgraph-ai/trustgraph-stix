
from pulsar.schema import Record, Bytes
from trustgraph.schema import Metadata

# This is the schema used for the stix-load queue
class StixDocument(Record):
    metadata = Metadata()
    stix = Bytes()

