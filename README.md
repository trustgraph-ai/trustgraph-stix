
Cybersecurity threat analysis with presentation to the knowledge
graph in STIX form.

# To use

To use:

- Build the software here to a container:

  podman build -f Containerfile -t docker.io/trustgraph/trustgraph-stix:0.0.0 .


- Configure TrustGraph, make sure to use STIX prompts in
  prompt-configuration.txt
  
- Need a high-end LLM, been testing with VertexAI Gemini models.

- Start TrustGraph

- Delete the kg-extract-definitions, kg-extract-relationships and
  kg-extract-topics processors.
  
- Start cyber-extract and stix-load

- Load the sample.txt file here with tg-load-text

Components:

- cyber-extract: Takes a text document and emits a STIX 2 bundle
- stix-load: Takes the STIX document from cyber-extract and maps to
  graph entities and triples.

What's broken:

- The processing in cyber-extraction and stix-load needs a lot of
  improvement.

- Could be better integrated with Config UI.







podman build -f Containerfile -t docker.io/trustgraph/trustgraph-stix:0.0.0 .


tg-show-processor-state

tg-show-flows




tg-show-flow-classes

tg-put-flow-class -n threat-analysis -c "$(cat ../stix/stix-flow-class.json)"


python3 load-stix-prompts

tg-stop-flow -i 0000
tg-start-flow -n threat-analysis -i 0000 -d 'STIX flow'

# Basic interface
tg-load-text -f 0000 sample.txt

tg-add-library-document \
    --identifier https://trustgraph.ai/doc/authentitator \
    --name 'Sample threat report' \
    --description 'A fictitous test data set mentioning the authentitor' \
    --kind text/plain \
    ../stix/sample.txt

tg-show-library-documents

tg-start-library-processing \
    --id threat01 \
    --flow-id 0000 \
    -d https://trustgraph.ai/doc/authentitator 

