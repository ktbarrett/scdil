# `scdil` - Simple Configuration and Data Interchange Language

A simple data interchange language that is effective at both human-to-program and program-to-program data interchange.
It is simpler than YAML, and more readible and writable than JSON.

scdil 1 will be both a superset of JSON and a subset of YAML 1.2.
Successive versions of scdil may introduce new features, but it will be backwards compatible with scdil 1.
Meaning that code to scdil 1 features will always be loadable with a YAML 1.2 parser like [`ruamel.yaml`](https://pypi.org/project/ruamel.yaml/).

This repo contains the [scdil specification document](spec.md) as well as a reference implementation in Python.
