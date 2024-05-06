# FINALES_Overlort_tenant
**Over** **L**ooking **Or**chestrating **T**enant
The Overlort tenant created for the use with FINALES


# Related Documents and Links to FINALES

Documents related to the FINALES project and its broader context can be found on the
respective Wiki page of the project:
[https://github.com/BIG-MAP/FINALES2/wiki/Links](https://github.com/BIG-MAP/FINALES2/wiki/Links)

Links to FINALES:

1. FINALES latest version Github
[https://github.com/BIG-MAP/FINALES2](https://github.com/BIG-MAP/FINALES2)

1. FINALES v1.1.0 Zenodo
[10.5281/zenodo.10987727](10.5281/zenodo.10987727)

1. Schemas of FINALES v1.1.0
[https://github.com/BIG-MAP/FINALES2_schemas](https://github.com/BIG-MAP/FINALES2_schemas)

Links to the other related tenants:

1. Optimizer Tenant
[https://github.com/BIG-MAP/F2Opt](https://github.com/BIG-MAP/F2Opt)

1. ASAB Tenant
[https://github.com/BIG-MAP/FINALES_ASAB_tenant](https://github.com/BIG-MAP/FINALES_ASAB_tenant)

1. Transportation Tenant
[https://github.com/BIG-MAP/FINALES_Transportation_tenant](https://github.com/BIG-MAP/FINALES_Transportation_tenant)

1. AutoBASS Tenant
[https://github.com/BIG-MAP/FINALES_AutoBASS_tenant](https://github.com/BIG-MAP/FINALES_AutoBASS_tenant)

1. Cycler Tenant
[https://github.com/BIG-MAP/FINALES_Cycler_tenant](https://github.com/BIG-MAP/FINALES_Cycler_tenant)

1. Degradation model Tenant
[https://github.com/BIG-MAP/eol_degradation_tenant](https://github.com/BIG-MAP/eol_degradation_tenant)


# Description

The Overlort tenant handels and replies to the Optimizer request by creating and handeling the necessary workflow. 
Open request ids are saved in lists together with the workflow id to enable handling of mulitple workflows.
All requests, intermediate results, the open request list and the final result are saved in a json file to restist (un)expected stops.
It constantly checks for new workflow requests, as well as results for open requests within running workflows. 
Once a new result is posted, it is picked up, saved and based on all available parameter of the workflow (and if necessary some calculations) the next quantity is requested. The schema for the next request is obtained from an endpoint of FINALES.
Content of the workflow are requests to the tenants of Cycler(Channel reservation),ASAB(elektrolyte mixing), Transportation(elektrolyte->AutoBASS), AutoBASS(cell assembly), again Transportation(cells->Cycler), Cycler(start,export,analysis) and Degradation_model(predict lifetime). For the cycler the Overlort creates one request for each cell defined in the AutoBASS result and also propergates this for the request of lifetime prediction. It summs all results up as one result for the optimizer.
A logger with self-designed messages is implemented to enable faster debugging and logging.

# Installation

To install the package, please follow the steps below.

1. Clone this repository
1. Install the packages reported in the requirements.txt
1. Fill in the blank spaces in the file `src\Overlort\configuration\config.py` according
to your setup.

# Usage 

To use the Overlort tenant, execute the script `src\Overlort\Overlort_reference.py`.

# Acknowledgements

This project received funding from the European Union’s
[Horizon 2020 research and innovation programme](https://ec.europa.eu/programmes/horizon2020/en)
under grant agreement [No 957189](https://cordis.europa.eu/project/id/957189) (BIG-MAP).
The authors acknowledge BATTERY2030PLUS, funded by the European Union’s Horizon 2020
research and innovation program under grant agreement no. 957213.
This work contributes to the research performed at CELEST (Center for Electrochemical
Energy Storage Ulm-Karlsruhe) and was co-funded by the German Research Foundation (DFG)
under Project ID 390874152 (POLiS Cluster of Excellence).
