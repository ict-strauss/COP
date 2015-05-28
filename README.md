# CONTROL ORCHESTRATION PROTOCOL (COP)

## Overview
The Control Orchestration Procotol (COP) abstracts a set of control plane functions used by an SDN Controller, allowing the interworking of heterogenous control plane paradigms (i.e., OpenFlow, GMPLS/PCE).

## YANG models for COP

- [service-call.yang](https://github.com/ict-strauss/COP/blob/master/yang-cop/service-call.yang)
- [service-topology.yang](https://github.com/ict-strauss/COP/blob/master/yang-cop/service-topology.yang)
- [service-path-computation.yang](https://github.com/ict-strauss/COP/blob/master/yang-cop/service-path-computation.yang)

## Using pyang swagger plugin

[Pyang](https://code.google.com/p/pyang/) is an extensible YANG validator and converter written in python. 

It can be used to validate YANG modules for correctness, to transform YANG modules into other formats, and to generate code from the modules. We have written a pyang plugin to obtain the RESTCONF API from a yang model. 

The RESTCONF API of the YANG model is interpreted with [Swagger](http://swagger.io/), which is a powerful framework for API description. This framework will be used to generate a Stub server for the YANG module.


## Build a Python server stub

We have created [json2python-codegen](https://github.com/ict-strauss/COP/tree/master/json2python-codegen) to allow the creation of a Python server stub from the obtained JSON swagger definition.


License
-------
The COP is a joint collaboration within [STRAUSS](http://www.ict-strauss.eu/) project. You can find the licenses of the different projects in each subfolder.
