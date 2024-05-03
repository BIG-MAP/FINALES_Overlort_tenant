from datetime import datetime
from pathlib import Path

conf = {}

conf["workflow"] = [
    ("cycling_channel", "service"),
    ("electrolyte", "flow", ['electrolyte']),
    ("transport", "transport_service"),
    ("cell_assembly", "autobass_assembly", ['electrolyte', 'anode', 'cathode']),
    ("transport", "transport_service"),
    ("capacity", "cycling"),
    ("degradationEOL", "degradation_model")
    ] # list of tuples with (quantity, method)

conf["general_meta"] = {
    "name": "Overlort - the workflow tenant",
    "description": "One tenant to rule them all."
    }

conf["sleep_time_s"] = 5

conf["FINALES_server_conf"] = {
    "host": "",
    "port": "",     
    }

conf["end_run_time"] = datetime(
    year="",
    month="",
    day="",
    hour="",
    minute="",
    second=""
    ) # fill in int

conf["operator"] = {
    "username": "",
    "password": "",
    "usergroups": [""]
    }

conf["tenant_user"] = {
    "username": "",
    "password": "",
    "usergroups": [""]
}
