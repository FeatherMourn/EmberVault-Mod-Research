# Emberworks runtime probes

These are separate Lua probe packages for the existing EML runtime. They are
observe-only and do not place, remove, capture, or mutate world content.

The Worldwright probe is the first runtime bridge. Its output must be collected
on a disposable test profile and compared with the offline capability report
before any mutating adapter is designed.
