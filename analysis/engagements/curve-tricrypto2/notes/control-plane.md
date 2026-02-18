# Control Plane — Curve Tricrypto2

## Auth Mechanisms
- Owner pattern with commit/apply/revert (2-step with delay)
- Kill switch with deadline

## Auth State Storage
- `owner`: current owner address
- `future_owner`: pending new owner
- `transfer_ownership_deadline`: timestamp for pending transfer
- `admin_actions_deadline`: timestamp for pending parameter changes
- `future_A_gamma_time`: timestamp for A/gamma ramp completion
- `kill_deadline`: hard deadline after which kill_me() no longer works
- `is_killed`: boolean kill state

## Auth Gates
| Function | Gate | Bypass Attempted | Result |
|----------|------|------------------|--------|
| ramp_A_gamma | owner only | TBD | |
| commit_new_parameters | owner only | TBD | |
| apply_new_parameters | owner only + deadline passed | TBD | |
| commit_transfer_ownership | owner only | TBD | |
| apply_transfer_ownership | owner only + deadline passed | TBD | |
| kill_me | owner only + before kill_deadline | TBD | |
| unkill_me | owner only | TBD | |

## Owner Identity
- TBD (will query from on-chain state)

## Bypass Hypotheses
1. Can commit/apply be called in same block? (delay check)
2. Is owner a multisig/DAO or EOA?
3. Can kill_deadline be bypassed?
4. claim_admin_fees is permissionless — can it be exploited?
