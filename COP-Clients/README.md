# COP Client examples

## Overview

This folder contains some client examples for testing the COP functionality.

## Notification Websocket Client

The class notificationClientFactory.py provides a simple example of a client generator for the notification server. It includes
a main example where two separated websocket clients are generated and connected to two fixed websocket server urls:
* 'ws://localhost:8181/restconf/streams/removeServiceCall/'
* 'ws://localhost:8181/restconf/streams/updateServiceCall/'

The clients connect to the websocket server and wait for a notification_stream arrives.
