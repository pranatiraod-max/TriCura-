# TriCura

## Algorithm Description
TriCura employs a **Discrete-Event Simulation** to schedule patients effectively among a limited pool of ER doctors (Trauma, Cardiology, and General). The algorithm operates by maintaining a queue of "ready" patients and advancing time efficiently from one critical event to another (e.g., patient arrivals, doctor availability, doctors completing rest), avoiding continuous per-minute checks.

At each discrete time event, the algorithm:
1. Updates the waitlist with any newly arrived patients who have entered the ER.
2. Sorts the waitlist primarily using a non-linear priority score.
3. Greedily attempts to match the highest-scoring patients with available doctors.

## Priority Scoring Formula
Patient priority is recalculated at each timestep using a severity-weighted scoring system:
`Score = (severity^3) * 1000 + severity * wait_time * 100`

This heavily prioritizes patients with high severity due to the cubic scaling of the severity factor. The wait time scales linearly, which helps break ties and slowly elevates the priority of lower-severity patients to prevent infinite queue starvation.

## Key Decisions & Rules
1. **Event-Driven Execution**: By jumping between important timestamps (`next_ev`), the scheduler optimizes performance and correctly sequences patients without wasting cycles on idle minutes.
2. **Specialist Priority & Generalist Fallback**: The algorithm strongly prefers matching patients to their strictly required specialist (e.g. TRAUMA to Doctor_T). A `GENERAL` doctor is utilized as a fallback only if:
   - The patient is highly critical (`severity >= 3`).
   - Or, the estimated wait time for the occupied requested specialist would exceed `3` time units.
3. **Fatigue & Rest Mechanic**: Supported via the optional `fc` (Fatigue Configuration) parameter. The algorithm tracks consecutive patient treatments. If a doctor surpasses workload constraints after a certain time (`after_min` and consecutive `limit`), they are assigned an inactive resting period (`rest`) before taking on the next patient.
4. **Overall Risk Tracking**: The algorithm tracks overall ER efficacy computing total risk. Individual risk overhead is calculated as `Severity * Actual Wait Time`. Minimizing overall wait-based risk forms the core goal of scheduling.

## Complexity
* **Time Complexity**: 
  The worst-case theoretical time complexity is **`O(N^2 log N)`**, where `N` is the number of patients. At each critical event, the unassigned active queue is reconstructed and re-sorted in `O(K log K)` time. Because assignments force a re-evaluation block via `while changed:` and there can be up to `2*N` discrete time events (one per arrival and treatment completion), the upper bound scales quadratically. However, practically it performs closer to `O(N log N)` as patients are continuously resolved.
* **Space/Memory Complexity**: 
  The space complexity is **`O(N)`** since the simulation tracks `N` total patient objects in memory (using separate waitlist arrays, complete tracking sets, and returning the structured schedule records). Doctor state is negligible `O(M)`.
