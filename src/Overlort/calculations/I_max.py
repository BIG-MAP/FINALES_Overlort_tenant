from pydantic import BaseModel, Field
from typing import Dict
from .default_values import default_values
import numpy as np

class I_max(BaseModel):
    parameter: Dict = Field(
        description="Dict with all Parameters.")
    
    def calculate(self, parameter):
        I_max = np.round(parameter['battery_chemistry']['cathode']['mass_loading'] * parameter['battery_chemistry']['cathode']['size'] * 10**(-3) * default_values["c_rate_charge"] * 1.2, default_values["roundnumber"])  # [mA / cm^-2] * [cm^2] * 10^-3 == A
        return(I_max)
