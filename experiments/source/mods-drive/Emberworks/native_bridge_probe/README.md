# Emberworks Native Bridge Probe

This is a deliberately inert Windows DLL build probe. It exposes only a version
marker and performs no hooks, game-memory writes, file writes, or runtime calls.

It is source/build verified only. Runtime registration remains unverified until
the EML loader's absolute-path registration behavior can be observed safely.
