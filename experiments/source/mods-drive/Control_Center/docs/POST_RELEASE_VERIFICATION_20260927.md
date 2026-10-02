# Post-release verification — working tree

The historical 1.0.1 release manifest records the 217-test suite that existed
when those artifacts were built. Subsequent research and authoring improvements
were made in the working tree. The active 1.0.2 manifest records the current
artifact hashes and release gate metadata.

Current working-tree verification:

- Python test suite: **364 tests passed**.
- Release artifact verifier: **1.0.2 valid**.
- GUI syntax compilation: passed after the Content Studio icon-path fix.
- CLI compiler smoke test: passed with a relative PNG icon.
- Research preview: rebuilt and launch/close tested separately.

The isolated 1.0.2 clean-install, upgrade-preservation, and uninstall run is
now complete and recorded in `docs/CLEAN_INSTALL_VERIFICATION_20260927.md`.
