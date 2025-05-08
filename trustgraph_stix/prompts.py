
sco_prompt="""You are tasked with creating STIX 2.1 Cyber-observable Objects
(SCOs) based on the provided threat intelligence write-up. SCOs include:
Artifact, Autonomous System, Directory, Domain Name, Email Address, Email
Message, File, IPv4 Address, IPv6 Address, MAC Address, Mutex, Network
 Traffic, Process, Software, URL, User Account, Windows Registry Key,
X.509 Certificate, HTTP Request, ICMP, Socket Ext, TCP Ext, Archive Ext,
Raster Image Ext, NTFS Ext, PDF Ext, UNIX Account Ext, Windows PE Binary Ext,
Windows Process Ext, Windows Service Ext, Windows Registry Ext,
JPEG File Ext, Email MIME Component, Email MIME Multipart Type,
Email MIME Message Type, Email MIME Text Type. Create relevant STIX 2.1 SCOs
in JSON format based on the information provided in the text. Strictly follow
the STIX 2.1 specification, ensuring no properties are used that are not
defined in the specification Ensure the JSON output is valid, starting with
[ and closing with ]. STIX SCO objects require at least type, id and value
properties. Only provide output if one or more SCOs can be identified with
 reasonable certainty from the text. Ensure the structure and format are
fully compliant with STIX 2.1.id STIX identifier must match
    <object-type>--<UUID>
Return only the JSON array, without any additional text, commentary, or
code block delimiters (e.g., json).

Text: {{text}}
"""

sdo_prompt="""You are tasked with creating STIX 2.1 Domain Objects (SDOs) from
the provided threat intelligence text.Possible SDOs include: Attack Pattern,
Campaign, Course of Action, Identity, Indicator, Intrusion Set, Malware,
Observed Data, Report, Threat Actor, Tool, Vulnerability, Infrastructure,
Relationship, Sighting, Note, Opinion, Grouping, Incident, Location, Malware
Analysis.Create relevant SDOs in JSON format, strictly adhering to the
STIX 2.1 specification. Ensure the output is a valid JSON array
([...]) containing only SDOs identified with high confidence. The is_family
field indicates whether the malware is a family (if true) or an instance
(if false). The values true or false are always enclosed in quotes. For id
property write just SDO_type-- following this example: "id": "malware--".
Timestamp must be in ISO 8601 format. Do not use created_by_ref and
source_ref. The labels property in malware is used to categorize or tag the
malware object with descriptive terms (e.g., "trojan", "backdoor",
"ransomware"), Must contain at least one string. threat-actor labels
property should be an array of strings representing categories or
descriptive terms for the threat actor. Return only the JSON array, without
any additional text, commentary, or code block delimiters (e.g., json).

Text: {{text}}
"""

sro_prompt="""You are tasked with creating a STIX 2.1 Relationship Object
(SRO) based on the provided writeup about threat intelligence text SDOs and
SCOs

Remember a relationship is a link between STIX Domain Objects (SDOs), STIX
Cyber-observable Objects (SCOs), or between an SDO and a SCO that describes
the way in which the objects are related. Relationships can be represented
using an external STIX Relationship Object (SRO) or, in some cases, through
certain properties which store an identifier reference that comprises an
embedded relationship, (for example the created_by_ref property).

Create STIX Objects, in json format. Identify Relationships: For each entity
(like intrusion-set, malware, infrastructure, domain-name, file, directory),
identify how they relate to each other. For example, malware might use
infrastructure for command and control, or an intrusion set might leverage
certain domains. Use relationship Objects: Use relationship objects to
connect entities. This object will specify the source and target entities and
define the nature of the relationship (e.g., "uses", "communicates
with"). Ensure Consistent Referencing: Make sure that every object you want
to relate is referenced correctly using their id in the relationship
objects. Pay attention to properties, do not use properties not defined in
STIX 2.1 specification. Start with [ and close with ] , no other content
before [ and after ]. If you cannot identify a specific SCO from the provided
text, simply do not do anything. Provide output only if you can identify one
or more SCOs with reasonable certainty. Pay attention to provide valid
json. Pay attention to provide valid STIX 2.1 structure. Return only the JSON
array, without any additional text, commentary, or code block delimiters
(e.g., json).

Input text:
{{text}}

SDO:
{{stix_sdo}}

SCO:
{{stix_sco}}
"""
