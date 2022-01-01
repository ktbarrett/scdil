# `scdil` - Simple Configuration and Data Interchange Language

A simple data interchange language that is effective at both human-to-program and program-to-program data interchange.
It is simpler than YAML, and more readible and writable than JSON.

scdil 1 will be both a superset of JSON and a subset of YAML.
Successive versions of scdil may introduce new features, but it will be backwards compatible with scdil 1.
Meaning that text sticking to scdil 1 features will always be loadable with a YAML parser.

This repo contains the [scdil specification document](spec.md) as well as a reference implementation in Python.
