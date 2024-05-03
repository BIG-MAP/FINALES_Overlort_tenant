from pydantic import BaseModel, Field
from typing import Dict
from .default_values import default_values
import numpy as np

class capacity(BaseModel):
    parameter: Dict = Field(
        description="Dict with all Parameters.")
    
    def calculate(self, parameter):
        capa = np.round(parameter['battery_chemistry']['cathode']['mass_loading'] * parameter['battery_chemistry']['cathode']['size'] * 10**(-4), default_values["roundnumber"])  # [mA / cm^-2] * [cm^2]
        return(capa)
