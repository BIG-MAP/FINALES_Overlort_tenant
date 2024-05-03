default_values = {
    "roundnumber": 5,
    'additional_electrolyte_volume_percentage': 0.1,
    'batch_volume': 8,
    "electrolyte_volume": 35,
    "cycling_protocol" : "BIG-MAP-Standard", 
    "number_cycles": 200,
    "V_max" : 4.2,
    "V_min" : 2.5,
    "c_rate_charge_formation" : 0.1,
    "c_rate_discharge_formation" : 0.1,
    "repetions_formation_cycle" : 3,
    "cycling_V_max" : 4.2,
    "cycling_V_min" : 2.5,
    "c_rate_charge" : 1,
    "c_rate_discharge" : 1,
}
default_values["number_required_channels"] = default_values["batch_volume"]