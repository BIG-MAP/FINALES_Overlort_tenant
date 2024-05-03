import json
import time
from datetime import datetime, timezone
from typing import Any, Callable, Optional, Union, cast, Dict
import os

import requests
from pydantic import BaseModel

from FINALES2.engine.main import RequestStatus, ResultStatus
from FINALES2.schemas import GeneralMetaData, Quantity, ServerConfig, Method, Quantity
from FINALES2.server.schemas import Request, Result
from FINALES2.user_management.classes_user_manager import User

from configuration.config import conf
from calculations import volume, CV_I_cutoff, CV_I_cutoff_formation, capacity, I_max
from calculations.default_values import default_values
import copy

from logging.config import dictConfig
import logging
import pytz
from Logger.logger import LogConfig

# Generate all the objects needed to instantiate the Overlort





class Overlort(BaseModel):
    """A class to represent a tenant for a FINALES run.

    :param BaseModel: The BaseModel of pydantic is used to provide type checking
    :type BaseModel: pydantic.BaseModel
    :return: An instance of a tenant object
    :rtype: Tenant
    """
    general_meta: GeneralMetaData = GeneralMetaData(name='Overlort', description='Workflow tenant')
    quantities:  Dict = {
    "degradationEOL": Quantity(
        name = "degradationEOL", 
        is_active = "True",
        methods = {
            "degradation_workflow": Method(
                name = "degradation_workflow",
                quantity = "degradationEOL",
                parameters =  [ "battery_chemistry", 
                               "input_cycles",
                                "average_charging_rate",
                                "maximum_charging_rate",
                                "minimum_charging_rate",
                                "delta_coulombic_efficiency",
                                "voltage_gap_charge_discharge",
                                "capacity_vector_variance",
                                "cell_info"
                ],
                limitations = {
                    "battery_chemistry": {
                        "electrolyte": [
                        [
                            {
                            "chemical": {
                                "SMILES": "C1COC(=O)O1",
                                "InChIKey": "KMTRUDSVKNLOMY-UHFFFAOYSA-N"
                            },
                            "fraction": [
                                {
                                "min": 0.0,
                                "max": 0.542
                                }
                            ],
                            "fraction_type": [
                                "molPerMol"
                            ]
                            },
                            {
                            "chemical": {
                                "SMILES": "[Li+].F[P-](F)(F)(F)(F)F",
                                "InChIKey": "AXPLOJNSKRXQPA-UHFFFAOYSA-N"
                            },
                            "fraction": [
                                {
                                "min": 0.0,
                                "max": 0.153
                                }
                            ],
                            "fraction_type": [
                                "molPerMol"
                            ]
                            },
                            {
                            "chemical": {
                                "SMILES": "CCOC(=O)OC",
                                "InChIKey": "JBTWLSYIZRCDFO-UHFFFAOYSA-N"
                            },
                            "fraction": [
                                {
                                "min": 0.35,
                                "max": 1.0
                                }
                            ],
                            "fraction_type": [
                                "molPerMol"
                            ]
                            }
                        ]
                        ],
                    "anode": {
                    "material": [
                        [
                        {
                            "chemical": {
                            "SMILES": [
                                "[C]"
                            ],
                            "InChIKey": [
                                "OKTJSMMVPCPJKN-UHFFFAOYSA-N"
                            ]
                            },
                            "fraction": [
                            {
                                "min": 1.0,
                                "max": 1.0
                            }
                            ],
                            "fraction_type": [
                            "molPerMol"
                            ]
                        }
                        ]
                    ],
                    "mass_loading": [
                        {
                        "min": 1.0,
                        "max": 1.0
                        }
                    ]
                    },
                    "cathode": {
                    "material": [
                        [
                        {
                            "chemical": {
                            "SMILES": [
                                "[Li+].[O-][Ni]=O"
                            ],
                            "InChIKey": [
                                "VROAXDSNYPAOBJ-UHFFFAOYSA-N"
                            ]
                            },
                            "fraction": [
                            {
                                "min": 1.0,
                                "max": 1.0
                            }
                            ],
                            "fraction_type": [
                            "molPerMol"
                            ]
                        }
                        ]
                    ],
                    "mass_loading": [
                        {
                        "min": 1.0,
                        "max": 1.0
                        }
                    ]
                    }
                },
                "input_cycles": [
                    [
                    {
                        "min": 0.0,
                        "max": 5.0
                    }
                    ]
                ],
                "average_charging_rate": [
                    {
                    "min": 0.1,
                    "max": 1.0
                    }
                ],
                "maximum_charging_rate": [
                    {
                    "min": 1.0,
                    "max": 1.0
                    }
                ],
                "minimum_charging_rate": [
                    {
                    "min": 0.1,
                    "max": 0.1
                    }
                ],
                "delta_coulombic_efficiency": [
                    {
                    "min": -1.0,
                    "max": 1.0
                    }
                ],
                "voltage_gap_charge_discharge": [
                    {
                    "min": 0.0,
                    "max": 1.0
                    }
                ],
                "capacity_vector_variance": [
                    {
                    "min": -150.0,
                    "max": 0.0
                    }
                ]
                }
    )
    }
    )
    }
    queue: list = []
    sleep_time_s: int =conf["sleep_time_s"]
    tenant_config: str = str(conf)
    authorization_header: Optional[dict] = None
    FINALES_server_config: ServerConfig = ServerConfig(host=conf["FINALES_server_conf"]['host'], port=conf["FINALES_server_conf"]['port'])
    end_run_time: datetime = conf["end_run_time"]
    operators: list = [User(**conf["operator"])]
    tenant_user: User = User(**conf["tenant_user"])
    tenant_uuid: str =""
    request_queue: list  = [] # list of lists with [request]  
    resultobjects: Dict = {}


    def tenant_object_to_json(self):
        """
        Funciton for creating the json input file, which is to be forwarded to the admin
        for registering a tenant.

        The uuid will be returned by the admin, which the user then will add to there
        Tenant object tenant_uuid field.
        """

        limitations = []
        capability_keys = list(self.quantities.keys())
        for capa_key in capability_keys:
            method_keys = list(self.quantities[capa_key].methods.keys())
            for method_key in method_keys:
                limitations.append(
                    {
                        "quantity": capa_key,
                        "method": method_key,
                        "limitations": self.quantities[capa_key]
                        .methods[method_key]
                        .limitations,
                    }
                )

        output_dict = {
            "name": self.general_meta.name,
            "limitations": limitations,
            "contact_person": str([u.username for u in self.operators]),
        }

        with open(f"{self.general_meta.name}_tenant.json", "w") as fp:
            json.dump(output_dict, fp, indent=2)
        
        return

    def _login(func: Callable):
        # Impelemented using this tutorial as an example:
        # https://realpython.com/primer-on-python-decorators/#is-the-user-logged-in
        def _login_func(self, *args, **kwargs):
            #print("Logging in ...")
            access_information = requests.post(
                (
                    f"http://{self.FINALES_server_config.host}:"
                    f"{self.FINALES_server_config.port}/user_management/authenticate"
                ),
                data={
                    "grant_type": "",
                    "username": f"{self.tenant_user.username}",
                    "password": f"{self.tenant_user.password}",
                    "scope": "",
                    "client_id": "",
                    "client_secret": "",
                },
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            access_information = access_information.json()
            self.authorization_header = {
                "accept": "application/json",
                "Authorization": (
                    f"{access_information['token_type'].capitalize()} "
                    f"{access_information['access_token']}"
                ),
            }
            return func(self, *args, **kwargs)

        return _login_func

    def _checkQuantity(self, request: Request) -> bool:
        """This function checks, if a quantity in a request can be provided by the
        tenant.

        :param request: a request object, which contains all the information relevant
        to the execution of the request
        :type request: Request
        :return: a boolean value stating, whether the requested quantity can be
        provided by the tenant
        :rtype: bool
        """
        requestedQuantity = request.quantity
        tenantQuantitites = self.quantities.keys()
        return requestedQuantity in tenantQuantitites

    def _checkMethods(self, request: Request, requestedQuantity: str) -> list[str]:
        """This function checks the methods in the request, if they are available in
        from the tenant and returns the names of the matching methods in a list.

        :param request: the requrest, which needs to be checked for feasibility
        :type request: Request
        :param requestedQuantity: the quantity, which shall be determined
        :type requestedQuantity: str
        :return: a list of the names of the methods, which can be performed by the
        tenant and are requested in the request
        :rtype: list[str]
        """
        tenantMethods = self.quantities[requestedQuantity].methods
        requestedMethods = request.methods
        # Collect all the matching methods in case the parameters are out of range
        # for the first method found.
        matchingMethods = []
        for method in requestedMethods:
            if method in tenantMethods:
                matchingMethods.append(method)
        return matchingMethods

    def _checkParameters(self, request: Request, method: str) -> bool:
        """This function checks the requested parameters for their compatibility
        with the tenant.

        :param request: a request containing the parameters to use when processing
        the request
        :type request: Request
        :param method: the method already identified as being compatible between the
        request and the tenant
        :type method: str
        :return: a boolean indicating, whether the parameters of the request are
        within the limitations of the tenant (True) or not (False)
        :rtype: bool
        """
        # TODO: Reactivate this check. This requires a parsing of the input and
        # limitations.
        # parametersCheck = []
        # requestParameters = request.parameters[method]
        # methodForQuantity = self.quantities[request.quantity].methods[method]
        # for p in requestParameters.keys():
        #     if isinstance(requestParameters[p], (float, int)):
        #         if isinstance(methodForQuantity.limitations[p], dict):
        #             tenantMin = methodForQuantity.limitations[p]["min"]
        #             tenantMax = methodForQuantity.limitations[p]["max"]
        #         elif isinstance(methodForQuantity.limitations[p], float):

        #         minimumOK = requestParameters[p] > tenantMin
        #         maximumOK = requestParameters[p] < tenantMax
        #         parametersCheck.append(minimumOK and maximumOK)
        # parametersOK: bool = all(parametersCheck)
        # return parametersOK
        return True
    
    @_login
    def _update_queue(self) -> None:
        """This function clears and recreates the queue of the tenant."""
        # empty the queue before recreating it to make sure, that all the requests
        # listed in the queue are still pending and were not worked on by another
        # tenant
        self.queue.clear

        # get the pending requests from the FINALES server
        pendingRequests = self._get_pending_requests()
        # update the queue of the tenant
        for pendingItem in pendingRequests:
            # create the Request object from the json string
            requestDict = pendingItem["request"]
            request = Request(**requestDict)

            # check, if the pending request fits with the tenant
            # check the quantity matches
            if not self._checkQuantity(request=request):
                continue

            # check, if the methods match with the tenant methods
            # This overwrites the request object. If an appropriate method was found
            # for the tenant, the methods list of the returned request only contains
            # the found method. Otherwise, the returned request is unchanged to the
            # original one
            matchedMethods = self._checkMethods(
                request=request, requestedQuantity=request.quantity
            )
            if matchedMethods == []:
                continue

            # check, if the parameters match with the tenant method
            for method in matchedMethods:
                if self._checkParameters(request=request, method=method):
                    request.methods = [method]
                    break

            # Reassemble the pendingItem to collect the full request in the queue with
            # only the method changed to the one, which can be performed by the tenant
            pendingItem["request"] = request.__dict__

            self.queue.append(pendingItem)

    @_login
    def _get_pending_requests(self) -> list[dict]:
        """This funciton collecte all the pending requests from the server.

        :return: a list of requests in JSON format
        :rtype: list[dict]
        """
        #print("Looking for tasks ...")
        # get the pending requests from the FINALES server
        pendingRequests = requests.get(
            f"http://{self.FINALES_server_config.host}"
            f":{self.FINALES_server_config.port}/pending_requests/",
            params={},
            headers=self.authorization_header,
        )
        return pendingRequests.json()

    # TODO: implement (input) validations.
    @_login
    def _post_request(
        self,
        quantity: str,
        methods: list[str],
        parameters: dict[str, dict[str, Any]],
    ) -> None:
        """This function posts a request.

        :param quantity: the name of the quantity to be requested
        :type quantity: str
        :param methods: a list of the method names acceptable for creating the result
        :type methods: list[str]
        :param parameters: a dictionary of the parameters, which shall be used when
            running the method; first key is the name of the method, the second level
            keys are the names of the parameters
        :type parameters: dict[str, dict[str, Any]]
        """

        request = Request(
            quantity=quantity,
            methods=methods,
            parameters=parameters,
            tenant_uuid=self.tenant_uuid,
        ).model_dump()

        _posted_request = requests.post(
            f"http://{self.FINALES_server_config.host}"
            f":{self.FINALES_server_config.port}/requests/",
            json=request,
            params={},
            headers=self.authorization_header,
        )
        _posted_request.raise_for_status()
        logger.info(f"Request is posted {_posted_request.json()}!")

    # TODO: implement (input) validations.
    @_login
    def _get_results(
        self,
        quantity: Union[str, None],
        method: Union[str, None],
        request_id: Union[str, None] = None,
    ) -> Union[list, dict]:
        """This function queries requests from the FINALES server. It my either provide
        a list of requests, if quantity and method is given, or a single request, if a
        request_id and optionally quantity and method are given. If there is no
        request_id and either quantity or method is None, a ValueError is raised

        :param quantity: the name of the quantity to be requested
        :type quantity: Union[str,None]
        :param method: the name of the method, by which the result was created
        :type method: Union[str,None]
        :param request_id: the id of the request, which asked for the result,
            defaults to None
        :type request_id: Union[str,None], optional
        :raises ValueError: A value error is raised, if information for requesting
            results by any of the available endpoints is impossible
        :return: _description_
        :rtype: Union[list,dict]
        """
        logger.info("Looking for results ...")
        if request_id is None:
            if (quantity is None) or (method is None):
                raise ValueError(
                    "No request ID was passed, therefore a quantity and method must "
                    "be specified."
                )
            # get the results from the FINALES server
            results = requests.get(
                f"http://{self.FINALES_server_config.host}"
                f":{self.FINALES_server_config.port}/results_requested/",
                params={"quantity": quantity, "method": method},
                headers=self.authorization_header,
            )
            return results.json()
        else:
            if (quantity is not None) or (method is not None):
                raise ValueError(
                    "A request ID was passed, therefore quantity and method must not "
                    "be specified."
                )
            # get the result for this ID from the FINALES server
            result = requests.get(
                f"http://{self.FINALES_server_config.host}"
                f":{self.FINALES_server_config.port}/results_requested/{request_id}",
                params={},
                headers=self.authorization_header,
            )
            return result.json()

    @_login
    def _post_result(self, request: dict, data: Any):
        """This function posts a result generated in reply to a request.

        :param request: a request dictionary specifying the details of the requested
                        data
        :type request: dict
        :param data: the data generated while serving the request
        :type data: Any
        """
        # transfer the output of your method to a postable result
        result_formatted = self._prepare_results(request=request, data=data)
        result_formatted["tenant_uuid"] = self.tenant_uuid

        # post the result
        _posted_result = requests.post(
            f"http://{self.FINALES_server_config.host}"
            f":{self.FINALES_server_config.port}/results/",
            json=result_formatted,
            params={},
            headers=self.authorization_header,
        )
        _posted_result.raise_for_status()
        logger.info(f"Result is posted {_posted_result.json()}!")

        # delete the request from the queue
        self.queue.remove(request)
        requestUUID = request["uuid"]
        logger.info(f"Removed request with UUID {requestUUID} from the queue.")

    @_login
    def change_status(self,requestID, new_status):
        reserved = requests.post("http://{}:{}/requests/{}/update_status/".format(conf["FINALES_server_conf"]["host"],conf["FINALES_server_conf"]["port"], requestID),
                                            params={'request_id' : requestID, 'new_status': new_status},
                                            headers=self.authorization_header,
                                            ).json()
        logger.info(reserved)
        
    @_login
    def _check_Input(self,request):
        quantity = request["quantity"]
        method = request["methods"][0]
        schemas = requests.get(
            "http://{}:{}/capabilities/templates".format(conf["FINALES_server_conf"]["host"],conf["FINALES_server_conf"]["port"]),
            params={'quantity': quantity, 'method': method},
            headers=self.authorization_header,
        ).json()
       
        
    def update_resultobject(self,result,resultobjects):
        logger.info('Updating result Object')
        for l in range(len(self.resultobjects)):
            original_request_id = self.resultobjects[l].keys()[0]
            for n in self.resultobjects[l][original_request_id].keys():
                if result['uuid'] == self.resultobjects[l][original_request_id][n]['request_uuid']:
                    self.resultobjects[l][original_request_id][n] = result
        
    def check_next_quantity(self,last_req,resultobjects_req):
        logger.info('Check next quantity after '+ str(last_req['quantity']))
        if resultobjects_req["request_0"]["request"]["request"]["quantity"] == conf['workflow'][0][0] and resultobjects_req["request_0"]["request"]["request"]["methods"][0]==conf['workflow'][0][1]: # inital request is step 0 in worklflow
            next_quantity = conf['workflow'][0][0]
            next_method =  conf['workflow'][0][1]
            return(next_quantity, next_method) 
        if last_req['quantity'] == "degradationEOL" and last_req['methods'][0]=="degradation_workflow": # inital request is step 0 in worklflow
            next_quantity = conf['workflow'][0][0]
            next_method =  conf['workflow'][0][1]
            return(next_quantity, next_method) 
        if "transport-1" in list(resultobjects_req.keys()) and "cell_assembly" in list(resultobjects_req.keys()) and "capacity" not in list(resultobjects_req.keys()): # checks for second transport
            next_quantity = conf['workflow'][5][0]
            next_method =  conf['workflow'][5][1]
            return(next_quantity, next_method) 
        for o in range(len(conf['workflow'])):   
            flag = False     
            if last_req['quantity'] in conf['workflow'][o] and last_req['methods'][0] in conf['workflow'][o] and o != 0: 
                for n in range(o,-1,-1): # runs backwards through workflow
                    if conf['workflow'][n][0] == list(resultobjects_req.keys())[-1] or conf['workflow'][n][0]=="capacity":
                        next_quantity = conf['workflow'][o+1][0]
                        next_method =  conf['workflow'][o+1][1]
                        flag = True
                        break
                    else:
                        next_quantity = conf['workflow'][0][0]
                        next_method =  conf['workflow'][0][1]
                if flag ==True:
                    break
            else:
                next_quantity = conf['workflow'][1][0]
                next_method =  conf['workflow'][1][1]
        return(next_quantity, next_method)       

    @_login
    def _update_new_request(self):
        """This function clears and recreates the queue of the tenant."""
        # empty the queue before recreating it to make sure, that all the requests
        # listed in the queue are still pending and were not worked on by another
        # tenant
        # get the pending requests from the FINALES server
        pendingRequests = self._get_pending_requests()
        # update the queue of the tenant
        validatedRequests = []
        for pendingItem in pendingRequests:
            # create the Request object from the json string
            requestDict = pendingItem["request"]
            request = Request(**requestDict)
            # check, if the pending request fits with the tenant
            # check the quantity matches
            if not self._checkQuantity(request=request):
                continue
            # check, if the methods match with the tenant methods
            # This overwrites the request object. If an appropriate method was found
            # for the tenant, the methods list of the returned request only contains
            # the found method. Otherwise, the returned request is unchanged to the
            # original one
            matchedMethods = self._checkMethods(
                request=request, requestedQuantity=request.quantity
            )
            if matchedMethods == []:
                continue
            # check, if the parameters match with the tenant method
            #for method in matchedMethods:
            #    if self._checkParameters(request=request, method=method):
            #        request.methods = [method]
            #        break
            #if _check_Input(requestDict):
            #    print("Input for Laura")
            #    break
            # Reassemble the pendingItem to collect the full request in the queue with
            # only the method changed to the one, which can be performed by the tenant
            pendingItem["request"] = request.__dict__
            validatedRequests.append(pendingItem)
        return validatedRequests
    
    @_login
    def _get_schema(self, quant , met):
        schema = requests.get(
                "http://{}:{}/capabilities/templates".format(conf["FINALES_server_conf"]["host"],conf["FINALES_server_conf"]["port"]),
                params={'quantity': quant, 'method': met},
                headers=self.authorization_header,
            ).json()
        return schema
    
    def copy_matching_keys(self,source, target):
            mismatch_keys=[]
            for key in source.keys():
                for targetkey in target.keys():
                    if key == targetkey:
                        if isinstance(source[key], dict):
                            for sourcekey in source[key].keys():
                                if sourcekey in target[key] :
                                    source[key][sourcekey] = target[key][sourcekey]
                                else:
                                    continue
                        else:
                            source[key] = target[key]                                             
                    elif key in globals():
                        function = globals()[key]
                        inst = function(parameter=target)
                        param_calc= inst.calculate(parameter=target)
                        source[key] = param_calc
                        #print('Calculated: '+ str(key))
                    elif key in default_values:
                        source[key] = default_values[key]
                    elif isinstance(target[targetkey], dict): # check if source key in subkey of target
                        for subtargetkey in target[targetkey].keys():
                            if key == subtargetkey:
                                if isinstance(source[key], dict) and isinstance(target[targetkey][subtargetkey], dict) and source[key].keys() == target[targetkey][subtargetkey].keys():
                                    source[key] =target[targetkey][subtargetkey]
                                elif isinstance(source[key], dict) and isinstance(target[targetkey][subtargetkey], list): 
                                    for subkey in source[key].keys():  # check if subkey in source is key yo
                                        if isinstance(source[key][subkey], list):
                                            for chemdic in source[key][subkey]:   # check if list of dicts have same keys
                                                for targetchemdic in target[targetkey][subtargetkey]:
                                                    if targetchemdic.keys() == chemdic.keys():
                                                        source[key][subkey] = target[targetkey][subtargetkey]
                                else:
                                    continue
                            else:
                                if isinstance(source[key], dict):
                                    self.copy_matching_keys(source[key], target)
                    elif isinstance(source[key], dict):
                        self.copy_matching_keys(source[key], target)
                    else:
                        mismatch_keys.append(key)
            return mismatch_keys, source, target
    
    def remove_optional_and_empty_keys(self,dictionary):
            keys_to_remove = []
            removed_keys = []
            for key, value in dictionary.items():
                if isinstance(value, str) and "optional" in value.lower():
                    keys_to_remove.append(key)
                    removed_keys.append(key)
                elif isinstance(value, dict):
                    # Recursively check and remove keys in nested dictionaries
                    sub_dict, sub_removed_keys = self.remove_optional_and_empty_keys(value)
                    dictionary[key] = sub_dict
                    removed_keys.extend([key + '.' + sub_key for sub_key in sub_removed_keys])
                elif value is None:
                    # Remove keys with None values
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del dictionary[key]
            return dictionary, removed_keys
    
    @_login  
    def request_quantity(self,quantity, method, resultobject, addInfo: str):
        logger.info('Starting to request quantity ' + str(quantity) +' with method '+ str(method))    
        schemas = self._get_schema(quant=quantity, met = method)
        inital_method = resultobject['request_0']['request']["request"]['methods'][0]
        initial_request_parameter = copy.deepcopy(resultobject['request_0']['request']["request"]['parameters'][inital_method])
        input_request = copy.deepcopy(schemas[str(quantity)+ '-'+ str(method)]['input_template'])    
        for capa in resultobject:
            if capa == "request_0": # checks if capa is empty or request_0
                continue
            elif capa == "capacity":
                if not resultobject[capa]["result"][addInfo]["result"] and resultobject[capa]["request"][addInfo]["request"]:
                    initial_request_parameter.update(resultobject[capa]["request"][addInfo]['parameters'][resultobject[capa]["request"][addInfo]['methods'][0]])
                elif resultobject[capa]["result"][addInfo]["result"]:
                    initial_request_parameter.update(resultobject[capa]["result"][addInfo]["result"]['data'])
                    continue
                else:
                    logger.error("resultobject has more keys than request and result or other error") 
            elif capa == "degradationEOL":
                    pass                    
            else:
                if not resultobject[capa]["result"] and resultobject[capa]["request"]:
                    try:
                        initial_request_parameter.update(resultobject[capa]["request"]['parameters'][resultobject[capa]["request"]['methods'][0]])
                    except:
                        pass
                elif resultobject[capa]["result"]:
                    initial_request_parameter.update(resultobject[capa]["result"]["result"]['data'])
                    continue
                else:
                    logger.error("resultobject has more keys than request and result or other error")   
        miss, input_request, initial_request_parameter = self.copy_matching_keys(input_request, initial_request_parameter)
        try:
            input_request['cell']['battery_chemistry']['electrolyte'] = input_request['cell']['battery_chemistry']['electrolyte']['formulation']
            input_request['cell_info']['electrolyte_info'] = initial_request_parameter['run_info']['formulation_info']
        except:
            pass
        if quantity == "capacity":
            logger.info("For request "+str(resultobject['request_0']['request']['uuid']))
            resultobject[quantity] = {
                "request": {},
                "result": {}
            }
            input_request['reservation_number']= initial_request_parameter["reservation_id"]  # change name in schemas at some point
            for cell in initial_request_parameter['batch_output']:
                input_request["cell_info"]= cell["cell_info"]
                try:
                    request_uuid = resultobject[quantity]["request"]['uuid']
                except:
                    request_uuid = resultobject['request_0']["request"]['uuid']
                
                request_next_quantity = {
                    "quantity": quantity,
                    "methods": [
                    method
                    ],
                    "parameters": {
                        method: input_request
                        }  ,
                    "tenant_uuid": self.tenant_uuid
                }
                requestID = requests.post(
                    "http://{}:{}/requests/".format(conf["FINALES_server_conf"]["host"],conf["FINALES_server_conf"]["port"]),
                    json=request_next_quantity,
                    params={},
                    headers=self.authorization_header
                ).json()
                # change requestID to cell uuuid
                resultobject[quantity]["request"][requestID] = request_next_quantity
                self.request_queue.append([requestID, resultobject['request_0']["request"]['uuid'] ])
                logger.info("Request for "+ str(quantity)+ " with requestID: "+ str(requestID)+ " successful")
                time.sleep(5)
        elif quantity == "degradationEOL" and method == "degradation_model":  
            logger.info("For request "+str(resultobject['request_0']['request']['uuid']))
            try:
                try:
                    if resultobject[quantity]: 
                        pass
                except:
                    resultobject[quantity] = {
                        "request": {},
                        "result": {}
                    }
            except:
                logger.error("Could not create request & result for requested quantitiy: "+ str(quantity))
                pass                
            try:
                request_uuid = addInfo
                input_request['battery_chemistry']['electrolyte'] = input_request['battery_chemistry']['electrolyte']['formulation']
                input_request["input_cycles"]=initial_request_parameter["capacity_list"]
            except:
                request_uuid = resultobject['request_0']["request"]['uuid']
            request_next_quantity = {
                "quantity": quantity,
                "methods": [
                method
                ],
                "parameters": {
                    method: input_request
                    }  ,
                "tenant_uuid": self.tenant_uuid
            }
            requestID = requests.post(
                "http://{}:{}/requests/".format(conf["FINALES_server_conf"]["host"],conf["FINALES_server_conf"]["port"]),
                json=request_next_quantity,
                params={},
                headers=self.authorization_header
            ).json()
            resultobject[quantity]["request"][str(requestID)] = {} 
            resultobject[quantity]["request"][str(requestID)] = request_next_quantity
            self.request_queue.append([requestID, resultobject['request_0']["request"]['uuid'] ])
            logger.info("Reqest for "+ str(quantity)+ " with requestID: "+ str(requestID)+ " successful")
        else:
            try:   
                if quantity == "transport" and resultobject["transport"]["result"]:
                    input_request['origin'] = initial_request_parameter['actual_new_location']
                    input_request['destination']['address'] = 'Cycler'
                    temp = resultobject.pop(quantity)
                    new_quant_name = quantity + "-1"
                    resultobject[new_quant_name] = temp
                    resultobject[quantity] = {
                    "request": {},
                    "result": {}
                    } 
                    
                else:
                    resultobject[quantity] = {
                    "request": {},
                    "result": {}
                }      
            except:
                resultobject[quantity] = {
                    "request": {},
                    "result": {}
                }
                try : 
                    input_request['destination']['address'] = 'AutoBASS'
                    input_request['origin'] = initial_request_parameter["electrolyte"]['location']
                except:
                    pass
            update_request, deleted_keys = self.remove_optional_and_empty_keys(input_request)  # could now also see witch keys were optinal and not set
            # check miss and remove keys
            if len(miss) > 0 :
                pass
                #logger.info("Still missing keys: "+ str(miss))
            try:
                request_uuid = resultobject[quantity]["request"]['uuid']
            except:
                request_uuid = resultobject['request_0']["request"]['uuid']   
            try:  
                request_next_quantity = {
                    "quantity": quantity,
                    "methods": [
                    method
                    ],
                    "parameters": {
                        method: input_request
                        }  ,
                    "tenant_uuid": self.tenant_uuid
                }
                requestID = requests.post(
                    "http://{}:{}/requests/".format(conf["FINALES_server_conf"]["host"],conf["FINALES_server_conf"]["port"]),
                    json=request_next_quantity,
                    params={},
                    headers=self.authorization_header
                ).json()
                resultobject[quantity]["request"] = request_next_quantity
                self.request_queue.append([requestID, resultobject['request_0']["request"]['uuid']])
                logger.info("For request "+str(resultobject['request_0']['request']['uuid'])+": Request for "+ str(quantity)+ " with requestID: "+ str(requestID) + " successful")
                time.sleep(5)
            except:
                now = datetime()
                current_time = now.strftime("%Y-%m-%d %H:%M:%S")
                filename = current_time + str(requestID)
                filepath = "/root/data/Overlort_26_07/src/Overlort/results_Overlort/failed_requests/" + filename
                with open(filepath, 'w') as fileobj:
                    json.dump(input_request, fileobj, indent=2)
                logger.error("Failed to post next request")

    @_login
    def _post_final_result(self,resultobject, requestid):
        logger.info("Post finale result")
        result_workflow = {
            "data": {
                "run_info": {},
                "degradationEOL": []
                },
            "quantity": "degradationEOL",
            "method": [
            "degradation_workflow"
            ],
            "parameters": {
                "degradation_workflow":
            {
            },
            },
            "tenant_uuid": self.tenant_uuid,
            "request_uuid": requestid
        }
        result_workflow["parameters"]["degradation_workflow"] = resultobject["request_0"]["request"]["request"]["parameters"][result_workflow["method"][0]]
        # copy run_info from electrolyte
        result_workflow['data']["run_info"] = resultobject["electrolyte"]["result"]["result"]["data"]["run_info"]
        for cell in list(resultobject["request_0"]["result"].keys()):
            celldata = {
            }
            celldata.update(resultobject["request_0"]["result"][cell]["result"]['data']["degradationEOL"])
            celldata["cell_info"]= {}
            celldata["cell_info"]= resultobject["request_0"]["result"][cell]["result"]["parameters"]["degradation_model"]["cell_info"]
            result_workflow['data']["degradationEOL"].append(celldata)
        print(len(result_workflow['data']["degradationEOL"]))
        filepath = "/root/data/Overlort/src/Overlort/results_Overlort/" + str("test") + ".json"
        with open(filepath, 'w') as fileobj:
            json.dump(result_workflow, fileobj, indent=2)
        print(filepath)

        resultID = requests.post(
            "http://{}:{}/results/".format(conf["FINALES_server_conf"]["host"],conf["FINALES_server_conf"]["port"]),
            json=result_workflow,
            params={},
            headers=self.authorization_header
        ).json()
        if resultID:
            logger.info("Posting final result successfull under ID " + str(resultID))
            return(resultID)
        else:
            logger.error("Failed to post final result")
            return("123123")

    @_login
    def _get_result(self,ID):
        result = requests.get(
                    "http://{}:{}/results_requested/{}".format(conf["FINALES_server_conf"]["host"],conf["FINALES_server_conf"]["port"], ID),
                    params={},
                    headers=self.authorization_header,
                ).json()
        return result
    
    def _save_overlort_params(self):
        filepath =  "overlort_info.json"
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S CET")
        overlort_params_dict = {
            "creation_time": current_time,
            "request_queue": self.request_queue,            
            "resultobjects": self.resultobjects
        }
        with open(filepath, 'w') as fileobj:
            json.dump(overlort_params_dict, fileobj, indent=2) 


    def run(self):
        """This function runs the tenant in a loop - getting all the requests from
        the server, checking them for their compatibility with the tenant and posting
        them to the server.
        """        
        logger.info('Overlort started')
        try:
            filepath = "overlort_info.json"
            with open(filepath, 'r') as fileobj:
                overlort_params = json.load(fileobj)
            self.request_queue = overlort_params["request_queue"]
            self.resultobjects = overlort_params["resultobjects"]
        except:
            filepath ="overlort_info.json"
            now = datetime.now()
            current_time = now.strftime("%Y-%m-%d %H:%M:%S")
            overlort_params_dict = {
                "request_queue": self.request_queue,
                "resultobjects": self.resultobjects,
                "creation_time": current_time
            }
            with open(filepath, 'w') as fileobj:
                json.dump(overlort_params_dict, fileobj, indent=2)     
        logger.info("Still pending requests: "+ str(self.request_queue))
        addInfo = ''
        while datetime.now() < self.end_run_time:
            # wait in between two requests to the server
            time.sleep(self.sleep_time_s)
            for req in self.request_queue:
                result_step = self._get_result(ID=req[0])
                if result_step:
                    if result_step["result"]["request_uuid"] == req[0] :
                        try:
                            result_quantity = result_step["result"]["quantity"]
                            result_method = result_step["result"]["method"][0]
                            if result_quantity == "capacity": # if capacity save the cell result at it´s uuid key
                                logger.info('Quantity is capacity')
                                self.resultobjects[req[1]][result_quantity]["result"][req[0]] = result_step
                                last_req = self.resultobjects[req[1]][result_quantity]["request"][req[0]]
                                addInfo = req[0]
                                next_quantity, next_method= self.check_next_quantity(last_req= last_req, resultobjects_req= self.resultobjects[req[1]])
                                logger.info("Next Quantity after "+str(result_quantity)+" is " +str(next_quantity)+ " and method "+ str(next_method))
                                try:   
                                    self.request_quantity(quantity=next_quantity,method=next_method, resultobject=self.resultobjects[req[1]], addInfo = addInfo)
                                    addInfo = ""
                                    index = self.request_queue.index(req)
                                    del self.request_queue[index]
                                    logger.info("Saved single capacity result with ID: " +str(req[0]))
                                except (Exception, KeyboardInterrupt):
                                    logger.error("Request for "+ str(next_quantity)+ " failed for request: "+ str(req[1]))
                                    try:
                                        del self.resultobjects[req[1]][next_quantity]
                                    except:
                                        print("Could not delete empty quantity")
                                        pass
                                    #self.change_status(r['uuid'], new_status = "pending" ) 
                                    raise
                                self._save_overlort_params()
                                
                            elif result_quantity == "degradationEOL" and result_method == "degradation_model":
                                logger.info("Quantity is degradationEOL")
                                counter = 0
                                for resultid in self.request_queue:
                                    if resultid[1] == req[1]:
                                        counter = counter +1
                                print(counter)
                                if counter > 1:
                                    # change req[0] at some point to some ID that is the same for capacity and degradation for better traceability
                                    try:
                                        self.resultobjects[req[1]][result_quantity]["result"][req[0]] = result_step
                                        for i in range(len(self.request_queue)):
                                            if self.request_queue[i][0] == req[0]:
                                                self.request_queue.pop(i)
                                                break
                                        logger.info("Saved single degradtion_model request with ID: "+ str(req[0]))
                                    except:
                                        logger.error("Could not save single degradation result of request: "+ str(req[0]))
                                    self._save_overlort_params()
                                else: # last result of the request is done, so final result must be posted
                                    try:
                                        self.resultobjects[req[1]][result_quantity]["result"][req[0]] = result_step
                                        self.resultobjects[req[1]]['request_0']['result'] = self.resultobjects[req[1]][result_quantity]["result"] # point on degradtionEOL results, no deepcopy for discspace reasons
                                    except:
                                        logger.error("Could not save last degradation single result")
                                    self._save_overlort_params()
                                    try:
                                        result_ID = self._post_final_result(self.resultobjects[req[1]], req[1])
                                        resultdict = {
                                            "request" : req[1],
                                            "result": result_ID,
                                            "workflow": self.resultobjects[req[1]]
                                        }
                                        originpath = os.getcwd()
                                        filepath = "/root/data/Overlort/src/Overlort/results_Overlort/" + str(self.resultobjects[req[1]]["request_0"]["request"]["ctime"].split("T")[0] +"_" + str(req[1]) + ".json")
                                        with open(filepath, 'w') as fileobj:
                                            json.dump(resultdict, fileobj, indent=2)
                                        os.chdir(originpath)
                                        self._save_overlort_params()
                                        index = self.request_queue.index(req)
                                        del self.request_queue[index]
                                        del self.resultobjects[req[1]]
                                        self._save_overlort_params()
                                    except:
                                        logger.error("Could not dump workflow data in file for request "+ str(req[1]))
                            else:
                                self.resultobjects[req[1]][result_quantity]["result"] = result_step
                                self._save_overlort_params()
                                if result_quantity == "capacity" or result_quantity == "degradation":
                                    last_req = self.resultobjects[req[1]][result_quantity]["request"][req[0]]
                                    addInfo = req[0]
                                else:
                                    last_req = self.resultobjects[req[1]][result_quantity]["request"]
                                next_quantity, next_method= self.check_next_quantity(last_req= last_req, resultobjects_req= self.resultobjects[req[1]])
                                logger.info('Next Quantity is ' +str(next_quantity)+ " and method "+ str(next_method))
                                try:   
                                    self.request_quantity(quantity=next_quantity,method=next_method, resultobject=self.resultobjects[req[1]], addInfo = addInfo)
                                    addInfo = ""
                                    index = self.request_queue.index(req)
                                    del self.request_queue[index]
                                except (Exception, KeyboardInterrupt):
                                    logger.error("Request for "+ str(next_quantity)+ " failed for request: "+ str(req[1]))
                                    try:
                                        del self.resultobjects[req[1]][next_quantity]
                                    except:
                                        print("Could not delete empty quantity")
                                        pass
                                    #self.change_status(r['uuid'], new_status = "pending" )
                                    raise
                                self._save_overlort_params()
                        except:
                            logger.error("Something went wrong when trying to post next quantity request")
                    else:
                        logger.error("ResultID and ID in request_queue are not the same")  
                else:
                    #print("no new results")
                    continue
            new_requests = self._update_new_request()
            for r in new_requests:
                logger.info("Creating new workflow for request " + str(r['uuid']))
                self.resultobjects[r['uuid']]= {}
                self.resultobjects[r['uuid']]['request_0'] = {
                    "request": {},
                    "result": {}
                }
                self.resultobjects[r['uuid']]['request_0']["request"] = r
                next_quantity, next_method= self.check_next_quantity(last_req =r['request'],resultobjects_req= self.resultobjects[r['uuid']])
                logger.info('Next Quantity is ' +str(next_quantity)+ " and method "+ str(next_method))
                self.resultobjects[r['uuid']][next_quantity]= {
                    "request": {},
                    "result": {}
                }
                self.resultobjects[r['uuid']][next_quantity]["request"]   
                try:   
                    self.request_quantity(quantity=next_quantity,method=next_method, resultobject=self.resultobjects[r['uuid']], addInfo = "")
                    self._save_overlort_params()
                    self.change_status(requestID = r['uuid'], new_status="reserved")
                    new_requests.remove(r)
                except (Exception, KeyboardInterrupt):
                    #self.change_status(r['uuid'], new_status = "pending" )
                    logger.error("Failed to change status to reserved")
                    try:
                        del self.resultobjects[r['uuid']]
                    except:
                        logger.error("Request "+str(r['uuid'])+ " could not be startet.")
                    raise

dictConfig(LogConfig().model_dump())
logger = logging.getLogger("Overlogger")
#logger.info("Dummy Info")
#logger.error("Dummy Error")
#logger.debug("Dummy Debug") 
#logger.warning("Dummy Warning")
logging.Formatter.converter = lambda *args: datetime.now(tz=pytz.timezone('CET')).timetuple()
logFileFormatter = logging.Formatter(
        fmt=f"%(levelname)s %(asctime)s (%(relativeCreated)d) \t %(pathname)s request: %(funcName)s - Info: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S CET",
    )

fileHandler = logging.FileHandler(filename='Overlort.log')
fileHandler.setFormatter(logFileFormatter)
fileHandler.setLevel(level=logging.INFO)

logger.addHandler(fileHandler)
overlort = Overlort()
overlort.run()
