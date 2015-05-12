# COP Server Generator for Python

Python code that uses json outputs from **pyang** to generate **RESTful server** and classes for the Control Orchestration Protocol

## Getting started

### How?

- Follow the COP indications from [COP main page](https://github.com/ict-strauss/COP) for the json generation.

- Run: `$ python COPGenerator.py jsonfile.json` with **jsonfile** as **service-call/topology/path-computation.json**

### Dependencies
 - This code generates python code that uses [web.py](http://webpy.org/install)

### Issues
- Some of the configurations are fixed for COP (e.g. type of return messages). To be fixed in next version.
- Does not support double hierarchy in class definitions (class inside a class).

### License

Copyright 2015 University of Bristol.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
