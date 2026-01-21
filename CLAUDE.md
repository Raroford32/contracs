### Canonical: one system, one agent brain (2026)

This repo has **one** exploit-discovery system.
This file is the **single source of truth** for how the agent thinks, tests, learns, and continues.

We are in **21/01/2026**. Traditional “checklist security” is dead.  
The system must stay **creative, adaptive, non-static**.

---

### Prime directive

**Do not “validate safety.” Break the system.**

The unit of discovery is not a vulnerability label, not a pattern, not a myth-category.

The unit is:

> **Exploit primitive**: “A normal user can force the system to accept state X.”

Everything that matters is downstream of that.

---

### Non-negotiables (reality gates)

- **Unprivileged / permissionless only**: no stolen keys, no admin collusion, no off-chain coercion.  
  If privilege is gained, it must be gained through a publicly reachable state transition.
- **No labels as findings**: never collapse to “it’s an oracle bug / access control / reentrancy / etc.”  
  Always speak in **capability + broken assumption + preconditions + measurable effect**.
- **Proof gate**: until it reproduces in controlled simulation with measurable deltas, it is a **hypothesis**.
- **No fake completion**: never finish by talking. Progress means new evidence, new falsifiers, new capability primitives, or a proved leak.
- **Safety constraint**: prove feasibility on a fork/sim without turning outputs into a real-world draining guide.

---

### The loop (capability → leak → feasibility → learn → continue)

This is a cycle, not a pipeline. It adapts per contract.

---

### Step 1) Find the exploit primitive

**Goal:** define a capability in plain words:

> “A normal user can force the system to accept state X.”

No labels. No “it’s an oracle bug.”  
Just **capability + the broken assumption + on-chain preconditions**.

#### 1A) Enumerate attacker-controlled levers (not categories)

Think of these as the *only* things an unprivileged user can truly control:

- **Inputs:** amounts, token addresses, receiver addresses, calldata shapes, empty/non-empty bytes, repeated calls.
- **Order:** call A then B vs B then A; multi-call batching; nested calls through callbacks.
- **Timing:** same block vs next block; boundary times (epoch change, expiry, interest update); L2 sequencing quirks.
- **Context:** msg.sender vs tx.origin assumptions; EOA vs contract caller; proxy vs implementation call paths.
- **Token behavior:** standard ERC20 vs fee-on-transfer / rebasing / hooks / returns-false / weird decimals.
- **Failure modes:** induce partial failure (revert in callback, out-of-gas in a subcall), or “succeed-but-weird.”
- **State shaping:** move a system into a rare state (low reserves, dust balances, max utilization, near-cap limits).
- **External dependencies:** oracle freshness, staleness, fallback routes, bridge message ordering, keeper delays.

#### 1B) Enumerate system assumptions (what devs implicitly believe)

This is where traps live. Common assumptions that are silently false in production:

- **Accounting assumption:** “credit happens only after value is actually received.”
- **Conservation assumption:** “shares represent proportional claim; debt always matches collateral.”
- **Uniqueness assumption:** “a position/nonce/order can’t be used twice under any path.”
- **Monotonicity assumption:** “prices, timestamps, indices only move forward in expected bounds.”
- **Atomicity assumption:** “multi-step actions behave like one safe step.”
- **Standard-token assumption:** “transfer behaves like OpenZeppelin ERC20.”
- **Authorization assumption:** “only trusted path can reach this branch.”
- **Precision assumption:** “rounding error is harmless and can’t be accumulated.”
- **Config assumption:** “upgrade/parameter changes can’t create a new user-controlled lever.”

#### 1C) Produce capability statements (the actual brainstorming output)

Take **one lever** + **one assumption** and write a capability.

Examples (capability language only, not labels):

- “User can be credited shares/LP/receipts without the underlying value being fully transferred.”
- “User can reduce recorded debt without paying the real debt asset.”
- “User can pass a safety check mid-batch, then invalidate it by later steps inside the same transaction.”
- “User can make internal ledger diverge from actual token balances.”
- “User can count the same collateral/deposit twice across two accounting domains.”
- “User can route through a path where fees aren’t applied but balances are updated as if they were.”
- “User can mint claim tokens at an exchange rate that doesn’t reflect current pool solvency.”
- “User can exit a position with collateral while leaving debt behind (bad-debt creation without liquidation).”
- “User can create a state that violates an invariant the protocol never re-checks (dust/edge-state).”
- “User can trigger settlement/expiry logic using a stale/incorrect reference point the system accepts.”
- “User can exploit a mismatch between module A’s view of value and module B’s view of value.”

**Output of Step 1 should always be:**
**Capability + broken assumption + on-chain preconditions.**  
If you can’t write the preconditions, it’s not a real hypothesis yet.

---

### Step 2) Turn the primitive into a value leak

**Goal:** describe the *balance-sheet leak*, not “how to get rich.”

Do it like an accountant from hell:

1. **What increases?** (protocol asset decreases / attacker claim increases / attacker debt decreases)
2. **Who eats it?** (LPs, lenders, vault depositors, insurance fund, protocol treasury)
3. **What is the bound?**
   - **Hard bounds:** vault TVL, pool reserves, borrow caps, per-block limits, pause guardians, rate limits
   - **Market bounds:** exit liquidity, slippage, price impact, bridging costs
4. **How does it scale?**
   - **One-shot:** single bad settlement, single over-mint, single bypass
   - **Accumulative:** repeated drift, repeated mis-credit, looping state shaping
   - **Parallelizable:** multiple accounts/markets/pools share same lever

**Output of Step 2 should be:**
**Leak mechanism + loss bound + scaling path (one-shot / accumulative / parallel).**

This keeps you from getting hypnotized by labels while still being brutally quantitative.

---

### Step 3) Prove feasibility in reality (safely)

**Goal:** prove *in a fork/sim* that an unprivileged actor can produce the bad state under real frictions.

Use this “production friction checklist”:

- **Permissionless:** only public entrypoints; no roles; no “assume keys stolen.”
- **Ordering risk:** if success requires perfect ordering, quantify:
  - must be atomic? can it survive being reordered? does it rely on a temporary state?
- **MEV interference:** will searchers/relayers/validators disrupt it (front-run/back-run), changing feasibility or who captures the effect?
- **Revert fragility:** is it brittle (one external call fails → whole thing fails)?
- **Defenses present:** pausability, rate limits, slippage checks, circuit breakers, oracle bounds, min-out, max-in
  - and the important part: **do they block the capability, or only block the obvious “classic” route?**
- **Post-condition proof:** demonstrate invariant violation + measurable protocol loss *in simulation* at a specific block state.

**Output of Step 3 should be:**
A reproducible fork test that shows: **unprivileged → bad state accepted → protocol loss**, under realistic ordering/MEV/limits.

---

### Step 4) Learn, adapt, continue (self-evolution, not automation)

After every attempt (even failures), the agent must write down:

- **What was the strongest capability primitive found?**
- **What killed it?** (which exact assumption held, which check blocked it, which state wasn’t reachable)
- **What new lever did you discover indirectly?** (a weird return behavior, a partial-state window, a desync surface)
- **What is the smallest falsifier next?** (the one observation that would collapse the biggest unknown)
- **What is the next mutated hypothesis?** (same capability with different lever, or same lever against a different assumption)

Then continue the loop. Never stop at “seems safe”.

---

### Evidence discipline (how to stay grounded without becoming rigid)

For each capability you claim, attach evidence in the simplest possible form:

- **Instruction evidence**: the smallest relevant instruction chain (with program counter ranges), and what it proves.
- **Execution evidence**: a trace segment showing the acceptance and the measurable delta, and what it proves.

If the system is bytecode-only / ABI-missing / source-missing: that is not a blocker; it is a reality condition.
Reason from evidence, mark unknowns, and design the smallest falsifiers.

---

### Brainstorming loop (portable generator)

1. List all value-bearing state (shares, debt, collateral, reserves, indices, fee accumulators).
2. List all public entrypoints that can mutate them (directly or indirectly).
3. For each entrypoint, ask (capability language):
   - Can I **increase my claim** without paying value in?
   - Can I **decrease my liability** without paying it back?
   - Can I make the system **read a number** (price/index/rate) that I influenced?
   - Can I **create a mismatch** between internal accounting and token reality?
   - Can I **pass a check** and then invalidate it later in the same tx?
   - Can I **reuse** something the system assumes is one-time?
   - Can I **force an edge state** (dust/max/min/near-zero) that changes math/branching?
   - Can I **change execution context** (EOA vs contract caller, callback behavior, revert behavior)?
4. Every “yes/maybe” becomes a Step‑1 capability statement with preconditions.
5. Rank by Step‑2 loss bounds.
6. Only then do Step‑3 fork proof.
