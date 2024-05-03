from pydantic import BaseModel, Field
from typing import Dict
from .default_values import default_values
from .capacity import capacity

class CV_I_cutoff_formation(BaseModel):
    parameter: Dict = Field(
        description="Dict with all Parameters.")
    
    def calculate(self, parameter):
        try:
            cutoff = parameter['CV_I_cutoff']
        except:
            capa = capacity.calculate(self, parameter)
            cutoff = round(capa/20,default_values["roundnumber"])
        return(cutoff)
