from pydantic import BaseModel, Field
from typing import Dict
from .default_values import default_values

class volume(BaseModel):
    parameter: Dict = Field(
        description="Dict with all Parameters.")
    
    def calculate(self, parameter):
        try:
            batchsize = parameter['batch_volume']
        except:
            batchsize = default_values['batch_volume']
        volume = round((2*(batchsize / 8))*(1+ default_values['additional_electrolyte_volume_percentage']),default_values["roundnumber"])+2
        return(volume)
