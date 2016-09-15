# CONTROL ORCHESTRATION PROTOCOL (COP)

## Overview
The Control Orchestration Procotol (COP) abstracts a set of control plane functions used by an SDN Controller, allowing the interworking of heterogenous control plane paradigms (i.e., OpenFlow, GMPLS/PCE).

The COP is defined using YANG models and RESTCONF. We provide the [YANG models](https://github.com/ict-strauss/COP/tree/master/yang) and a set of tools to process the YANG models and obtain the necessary classes and interfaces that will support the COP. These tools are:
 - Pyang plugin for Swagger
 - JSON to Python code generator

## COP YANG models

The [COP YANG models](https://github.com/ict-strauss/COP/tree/master/yang) are available for discussion to research community. Up to now three YANG models have been discussed:

- [service-call.yang](https://github.com/ict-strauss/COP/blob/master/yang/yang-cop/service-call.yang)
- [service-topology.yang](https://github.com/ict-strauss/COP/blob/master/yang/yang-cop/service-topology.yang)
- [service-path-computation.yang](https://github.com/ict-strauss/COP/blob/master/yang/yang-cop/service-path-computation.yang)

## Pyang plugin for Swagger - DEPRECATED 
This plugin has been contributed to [OpenSourceSDN.org Project EAGLE](https://github.com/OpenNetworkingFoundation/EAGLE-Open-Model-Profile-and-Tools/tree/YangJsonTools).



## JSON to Python code generator - DEPRECATED
This code generator has been contributed to [OpenSourceSDN.org Project EAGLE](https://github.com/OpenNetworkingFoundation/EAGLE-Open-Model-Profile-and-Tools/tree/JsonCodeTools).



License
-------
The COP is a joint collaboration within [STRAUSS](http://www.ict-strauss.eu/) project. You can find the licenses of the different projects in each subfolder.
