
# Cybersecurity threat analysis with TrustGraph

This has been maintained to be an example of adding external processing
components to a running TrustGraph system.

Takes threat reports and converts to something that can load to the
knowledge graph in STIX form.  Everything here is designed to work
with TrustGraph 0.23 and beyond and makes use of recent APIs.

## To use

To use:

- Build the software here to a container:

```
  podman build -f Containerfile -t docker.io/trustgraph/trustgraph-stix:0.0.0 .
```

- You need to use a high-end LLM, been testing with VertexAI Gemini models.

- Configure TrustGraph.  Modify the resources so that stix-load,
  cyber-extract and tg-init-cyberthreat are started at boot time.
  
  To do this to a TrustGraph docker-compose file, use the patch file here.

```  
  patch -p1 docker-compose.yaml < stix.patch  
```

- Start TrustGraph

- Wait until the system is running (e.g. check `tg-show-flows`).

- Check the `threat-analysis` flow class has been loaded:

```
tg-show-flow-classes
```
  
- Stop the default flow and replace it with a threat analysis flow:

```
tg-stop-flow -i 0000
tg-start-flow -n threat-analysis -i 0000 -d 'STIX flow'
```

- Load the sample document and process:

```
tg-add-library-document \
    --identifier https://trustgraph.ai/doc/authentitator \
    --name 'Sample threat report' \
    --description 'A fictitous test data set mentioning the authentitor' \
    --kind text/plain \
    sample.txt
```

```
tg-show-library-documents
```

```
tg-start-library-processing \
    --id threat02 \
    --flow-id 0000 \
    -d https://trustgraph.ai/doc/bad
```

- Wait 30 seconds or so, check the graph has some data:

```
tg-show-graph
```

- Ask a question:

```
tg-invoke-graph-rag -q 'Describe threat actors using the authentiator'
```

## Internals

Components:

- cyber-extract: Takes a text document and emits a STIX 2 bundle
- stix-load: Takes the STIX document from cyber-extract and maps to
  graph entities and triples.
- tg-init-cyberthreat: Runs at boot time to add prompts and flow-classes
  to the system.

What's broken:

- The processing in cyber-extraction and stix-load needs a lot of
  improvement.

- Could be better integrated with Config UI.


