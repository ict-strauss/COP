# COP usage examples

## Create a Service Call

curl -X PUT -H "Content-type:application/json" -u admin:pswd1 http://localhost:8080/restconf/config/calls/call/call_1/ -d '{"callId":"call_1","aEnd":{"routerId":"10.0.50.1","interfaceId":"1","endpointId":"ep1"}, "zEnd":{"routerId":"10.0.50.2","interfaceId":"2","endpointId":"ep2"}, "trafficParams":{"latency":100,"reservedBandwidth":100000000},"transportLayer":{"layer":"ethernet"}}'

## Create a Connection
curl -X PUT -H "Content-type:application/json" -u admin:pswd1 http://localhost:8080/restconf/config/connections/connection/conn_1/ -d '{"connectionId":"conn_1", "aEnd":{"routerId":"10.0.50.1","interfaceId":"1","endpointId":"ep1"}, "zEnd":{"routerId":"10.0.50.2","interfaceId":"2","endpointId":"ep2"}, "path":{"topoComponents":[{"routerId":"10.0.50.1","interfaceId":"1","endpointId":"ep1"}, {"routerId":"10.0.50.3","interfaceId":"1","endpointId":"ep3"},{"routerId":"10.0.50.2","interfaceId":"2","endpointId":"ep2"}], "multiLayer":false, "noPath":false, "label":{"labelType":1, "labelValue":15}}}'

## Get Connection information

curl -X GET -H "Content-type:application/json" -u admin:pswd1 http://localhost:8080/restconf/config/connections/connection/conn_1/

## Request topology

curl -X GET -H "Content-type:application/json" -u admin:pswd1 http://localhost:8080/restconf/config/topologies/topology/topo_1/

## Notifications

### OSNR

### PLR (Packet Loss Ratio)
