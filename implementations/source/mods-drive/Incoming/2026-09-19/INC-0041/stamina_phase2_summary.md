Based on the full extraction and static classification of the 26 references to the Stamina hash `0x04B6AA8B`, I have successfully triaged the candidates down to the authoritative mutation paths. I am stopping before implementing any mutations or hooks.

### Comprehensive RVA Classification Table (Build 1076226)

| **RVAClassificationRead/Write EvidenceArithmetic EvidenceRelevant Call/BranchConfidenceDecision** |                           |                                           |                                               |                     |      |           |
| ------------------------------------------------------------------------------------------------- | ------------------------- | ----------------------------------------- | --------------------------------------------- | ------------------- | ---- | --------- |
| `0x1E0DFC`                                                                                        | `INITIALIZATION`          | Writes constants (`0x3f800000`) to memory | None                                          | None                | High | Eliminate |
| `0x1E4CB5`                                                                                        | `READ_ONLY`               | Stack copy only                           | None                                          | None                | High | Eliminate |
| `0x1F5731`                                                                                        | `READ_ONLY`               | Stack copy only                           | None                                          | None                | High | Eliminate |
| `0x1F9C57`                                                                                        | `READ_ONLY`               | Stack copy only                           | None                                          | None                | High | Eliminate |
| `0x1FA1BB`                                                                                        | `INITIALIZATION`          | Writes pointer offset to `[rax+0xc]`      | None                                          | None                | High | Eliminate |
| `0x1FA22B`                                                                                        | `INITIALIZATION`          | Writes pointer offset to `[rax+0xc]`      | None                                          | None                | High | Eliminate |
| `0x210CCC`                                                                                        | `READ_ONLY`               | Memory to register read                   | None                                          | None                | High | Eliminate |
| `0x234212`                                                                                        | `ATTRIBUTE_SELECTOR`      | Discovered in Phase 1; stack copy         | None                                          | `call 0xfe5fe0`     | High | Eliminate |
| `0x23634A`                                                                                        | `READ_ONLY`               | Memory to register read                   | None                                          | None                | High | Eliminate |
| `0x274674`                                                                                        | `INITIALIZATION`          | Writes property index to `[rbp-0x50]`     | None                                          | None                | High | Eliminate |
| `0x274ECB`                                                                                        | `INITIALIZATION`          | Writes to `[rax+0x4a0]`                   | None                                          | None                | High | Eliminate |
| `0x27D224`                                                                                        | `READ_ONLY`               | Stack copy only                           | None                                          | None                | High | Eliminate |
| `0x2915B1`                                                                                        | **`DIRECT_WRITE`**        | **Reads property, writes to ****`[rax]`** | **`addss`****, ****`mulss`**                  | Vector math/`sqrtf` | High | **KEEP**  |
| `0x291828`                                                                                        | `READ_ONLY`               | Stack copy only                           | None                                          | None                | High | Eliminate |
| `0x2C829F`                                                                                        | `READ_ONLY`               | Stack copy only                           | None                                          | None                | High | Eliminate |
| `0x2E3D7E`                                                                                        | `READ_ONLY`               | Stack copy only                           | None                                          | None                | High | Eliminate |
| `0x2E3DDA`                                                                                        | **`DIRECT_WRITE`**        | **Writes ****`[r13+4]`**** after math**   | **`subss`**                                   | None                | Med  | **KEEP**  |
| `0x2F1632`                                                                                        | **`COST_CALC_CANDIDATE`** | Reads property, intermediate writes       | **`subss`****, ****`mulss`****, ****`maxss`** | `call 0xcb01d0`     | Med  | **KEEP**  |
| `0x2F1AB0`                                                                                        | `INITIALIZATION`          | Loop writing `[r8+rcx*4]`                 | None                                          | None                | High | Eliminate |
| `0x2F1B93`                                                                                        | `INITIALIZATION`          | Loop writing `[r8+rcx*4]`                 | None                                          | None                | High | Eliminate |
| `0x365313`                                                                                        | `INITIALIZATION`          | Stack offset setup                        | None                                          | None                | High | Eliminate |
| `0x38ADE0`                                                                                        | `READ_ONLY`               | Event/Trace serialization                 | None                                          | None                | High | Eliminate |
| `0x38B36E`                                                                                        | `READ_ONLY`               | Event/Trace serialization                 | None                                          | None                | High | Eliminate |
| `0x38BA06`                                                                                        | `READ_ONLY`               | Event/Trace serialization                 | None                                          | None                | High | Eliminate |
| `0x398901`                                                                                        | `READ_ONLY`               | Network/State sync                        | None                                          | None                | High | Eliminate |
| `0x398962`                                                                                        | `READ_ONLY`               | Network/State sync                        | None                                          | None                | High | Eliminate |

---

### Top 3 Mutation Candidates

#### 1. `0x2915B1` (Highest Priority - The Distance Drain Authority)

- **Why it survived triage**: Immediately after resolving the Stamina hash, this path resolves a second hash (`0xb8388248` - highly likely to be `DistanceDrainRate`). It then calculates a 3D displacement vector magnitude using `mulss xmm7, xmm7` ... `sqrtss xmm0, xmm7`. It multiplies the displacement by the secondary rate and delta-time.
- **The Write**: It performs `addss xmm6, dword ptr [rax]` and strictly writes back to the resolved stamina component: `movss dword ptr [rax], xmm6`. *(Note: **`addss`** with a negative operand constitutes a decrement).*
- **Glider Correlation**: This represents exactly the `DistanceDrain * Distance` formula we hypothesized was vanishing when the Glider's forward speed was zeroed.

#### 2. `0x2E3DDA` (Medium Priority - The Temporal Drain Authority)

- **Why it survived triage**: This site features a direct `subss xmm0, xmm1` instruction operating on the resolved stamina component, followed immediately by an arithmetic write-back to an offset. It contains none of the spatial physics math found in `0x2915B1`.
- **Glider Correlation**: This is the strongest candidate for the residual "base temporal drain" that persists during gliding even when horizontal displacement falls to zero.

#### 3. `0x2F1632` (Medium Priority - Action Cost / Clamp)

- **Why it survived triage**: Features extensive math (`subss`, `mulss`, `maxss`) and calculates a heavily bounded threshold using `[rax+0x10]` clamps.
- **Glider Correlation**: Less likely to be the continuous physics drain, but highly likely to be the action-cost verification path (e.g., ensuring you have minimum stamina to *deploy* the glider or jump).

---

### Exact Next Observe-Only Experiment

To distinguish which site causes the residual Glider drain without modifying gameplay logic, we will install a strictly observe-only hook array.

**Exact Probe Sites:**

1. **Probe A (Distance Drain)**: `0x291678` (Targeting `addss xmm6, dword ptr [rax]`)
2. **Probe B (Temporal Drain)**: `0x2E3EA6` (Targeting `subss xmm0, xmm1`)

**What the probe records:** Using the register-neutral hook primitive, the trampoline will capture:

- `rax` (The candidate stamina address).
- `xmm6` (Probe A) or `xmm1` (Probe B) to reveal the exact delta being applied.
- The raw float value before the math (`[rax]`).
- Execution count/timestamp (to avoid trace flooding).

**Discriminating Result (The Accept/Reject Gate):** You will perform a controlled sequence: Idle -> Sprint -> Recover -> Ordinary Glide -> Glide with `0x39E73C` (zeroed displacement) active.

- **Confirmation of Probe A**: If Probe A fires continuously during a sprint and ordinary glide, but its `xmm6` delta drops to exactly `0.0f` during the zeroed-displacement glide, it is unequivocally the distance-drain component.
- **Confirmation of Probe B**: If Probe B fires continuously during ordinary gliding, and *continues* to fire at the exact same rate during the zeroed-displacement glide, it is the authoritative temporal baseline drain.

If you approve this specific discrimination strategy, I can provide the `.c` implementations to insert these register-neutral probes into `ArchitectNativeRuntime`.