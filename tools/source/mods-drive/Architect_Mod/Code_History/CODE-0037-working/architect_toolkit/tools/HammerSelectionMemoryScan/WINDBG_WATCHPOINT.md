# Hammer-selection writer watchpoint

The scanner is read/query-only. After it reports one or more candidates, use a
debugger only to observe the next manual selection transition; do not patch the
candidate or resume with modified registers.

For the current-session candidate (`client object 0x3002ECADC00`, field
`+0x1C`), set the first breakpoint at `0x3002ECADC1C`:

```text
ba w4 0x3002ECADC1C
g
r
kv
u @rip-30 @rip+40
dq 0x3002ECADC1C-40 L20
```

Run the sequence twice in the same game session:

1. Ceiling 2m (`3338618487`) → Ring (`1458989991`)
2. Ring (`1458989991`) → Sphere (`2719914608`)

Record the instruction RVA (`RIP - enshrouded.exe base`), a likely containing
function boundary, the base register and displacement used by the writer, the
register holding the incoming item ID, and the caller stack. A common writer on
both transitions is evidence for a legitimate selection setter; it is not
authorization to patch it.

If Enshrouded has restarted, do not reuse the old virtual address. Rediscover
it with the scanner:

```powershell
.\tools\HammerSelectionMemoryScan\Run-HammerSelectionMemoryScan.ps1 -Pid (Get-Process enshrouded).Id -A 3338618487 -B 1458989991 -C 2719914608
```

Use a surviving naturally aligned candidate from
`bridge/hammer_selection_memory_scan.json` in the `ba w4` command.
