
STIX extraction, very rough, bare structure is there.

To use:

- Configure TrustGraph, make sure to use STIX prompts in
  prompt-configuration.txt
  
- Need a high-end LLM, been testing with `gemini-1.5-pro-002` in
  Google AI Studio.  Gemini Flash seems to produce broken STIX.

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

