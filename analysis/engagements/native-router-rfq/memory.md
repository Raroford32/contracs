# Memory (native-router-rfq) — HALTED

## Pinned Reality
- chain_id: 1
- fork_block: (not pinned — local RPCs unreachable from sandbox)
- attacker_tier: reality-based; default public mempool, escalate with evidence
- target (declared): Native Router @ 0x1080808080f145b14228443212e62447c112adad

## Result of Phase B (Bundle)
HALTED. Address-to-protocol heuristic was wrong:

| Address | Asserted by me | Actual on-chain |
|---|---|---|
| 0x1080808080f145b14228443212e62447c112adad | Native Router | **No code, no txs.** Address is empty on mainnet. |
| 0x755569159598f3702bdd7dff6233a317c156d3dd | Hashflow Router | Has code but **unverified** on Etherscan/Sourcify. |
| 0xbeefb45b6f9acb175e70acf16dc20d6120044c70 | Bebop Blend | Verified as **MetaMorphoV1_1** (Morpho vault, not RFQ). |
| 0xdef1fce2df6270fdf7e1214343bebbab8583d43d | 0x Settler v1 | Verified as **MetaMorphoV1_1** (Morpho vault, not 0x). |
| 0x9008d19f58aabd9ed0d60971565aa8510560ab41 | CoW GPv2Settlement | **Confirmed** — GPv2Settlement, source available (102307 chars). |

(0xdef1fce + 0xbeefb45b returning identical MetaMorpho source is likely Etherscan SimilarMatch fallback or actual Morpho vault deployments at vanity addresses — they are NOT 0x/Bebop.)

## What this means
None of the addresses I picked from the list are verified "custom RFQ swap proxies" except CoW (which is a batch-auction settlement, well audited).

Options to unblock:
1. Pick a different known RFQ proxy — user provides the exact address (I will verify it's in the list and verified).
2. Permit a systematic scan of all 2812 addresses for RFQ markers (selectors like `fillRFQOrder`, `settleRFQT`, `traderQuote`, EIP-712 RFQ domain names). Expensive: would need bulk Etherscan queries (~2812 * source fetches). Cost: 1-2h elapsed plus rate limits.
3. Switch target to CoW GPv2Settlement (verified, in the list) — but it's not "custom" in the way you described.
4. Reverse-engineer 0x755569... bytecode anyway via evm-bytecode-lab — would yield selector inventory but no semantic understanding without sources.

## Open Unknowns
- Working RPC endpoint accessible from this sandbox (local RPCs in `etherscanrpc.md` are TCP-blocked).
- Real address of "the custom RFQ swap proxy" the user has in mind (if it's a specific deployment).
