# Emberworks standalone packages

The folders in this repository are independent mod packages. They share the
`construction_sdk` contracts but do not import Control Center.

## Current build

The current release is an offline/simulated foundation. It can be installed as
a Python package for development and testing, but it is not yet an Enshrouded
runtime mod. Runtime placement, world capture, persistence, multiplayer, and
dedicated-server behavior remain unverified.

The SDK deliberately exposes an unavailable-runtime adapter and capability
checks. Do not treat simulated placement as in-game placement; a live adapter
must first pass the runtime evidence gate.

## Package groups

- `construction_sdk`: shared contracts.
- `blueprint_library`: storage and revision management.
- `worldwright`: selection and WorldEdit-style offline operations.
- `zooping`: batch construction generators.
- `builders_wand`: bounded player-tool operations.
- `chiselcraft`: 16×16×16 microstructure editing.
- `framed_architecture`: shape and appearance compatibility.
- `restoration`: structure comparison and repair planning.
- `kinetic_works`: offline mechanical simulation.

For a development install, install the wheel from
`dist/emberworks_mods-0.1.0-py3-none-any.whl`. The packaged wheel has been
verified to import all nine public packages.
