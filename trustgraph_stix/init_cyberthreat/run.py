#!/usr/bin/env python3

"""
Loads cyberthreat analysis prompts into the system.
"""

from trustgraph.api import Api, ConfigKey, ConfigValue
import trustgraph_stix.prompts as prompts
import importlib

import os
import json
import argparse

# This is a flag so we know if things have to be re-configured
current_version = "v1"

files = importlib.resources.files()
resources_dir = files.joinpath("..").joinpath("resources")
class_def_path = resources_dir.joinpath("stix-flow-class.json")

with open(class_def_path, "r") as f:
    class_def = json.load(f)

default_url = os.getenv("TRUSTGRAPH_URL", 'http://api-gateway:8088/')

def set_prompt(api, id, prompt, response):

    values = api.get([
        ConfigKey(type="prompt", key="template-index")
    ])

    ix = json.loads(values[0].value)

    object = {
        "id": id,
        "prompt": prompt,
    }

    if response:
        object["response-type"] = response
    else:
        object["response-type"] = "text"

    if id not in ix:
        ix.append(id)

    values = api.put([
        ConfigValue(
            type="prompt", key="template-index", value=json.dumps(ix)
        ),
        ConfigValue(
            type="prompt", key=f"template.{id}", value=json.dumps(object)
        )
    ])

def configure(url):

    api = Api(url)
    config = api.config()
    flow = api.flow()

    val = config.get([ConfigKey(type="init-state", key="cyberthreat")])

    if val[0].value == current_version:
        print("Already configured - nothing to change")
        return

    set_prompt(config, "stix-sco", prompts.sco_prompt, "json")
    set_prompt(config, "stix-sdo", prompts.sdo_prompt, "json")
    set_prompt(config, "stix-sro", prompts.sro_prompt, "json")

    print("Prompts set")

    config.put([
        ConfigValue(
            type="flow-classes", key="bunch", value=json.dumps(class_def)
        )
    ])

    print("Flow class configured")

    val = config.put([
        ConfigValue(
            type="init-state", key="cyberthreat", value=current_version
        )
    ])

    print("All done.")

def run():

    parser = argparse.ArgumentParser(
        prog='tg-init-cyberthreat',
        description=__doc__,
    )

    parser.add_argument(
        '-u', '--api-url',
        default=default_url,
        help=f'API URL (default: {default_url})',
    )

    args = parser.parse_args()

    try:

        configure(
            url=args.api_url,
        )

    except Exception as e:

        print("Exception:", e, flush=True)



