
# The standard TrustGraph schema doesn't have a name for the queue
# that's used between cyber-extract and stix-load, that's defined here...
stix_ingest_queue = topic('stix-load')

# This is the schema used for the stix-load queue
class StixDocument(Record):
    metadata = Metadata()
    stix = Bytes()

