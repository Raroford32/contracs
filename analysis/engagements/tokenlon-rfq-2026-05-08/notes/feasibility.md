# Feasibility — RFQ swap-proxy attack tier ledger

For each top hypothesis, document attacker tier, ordering, oracle, capital,
and the cheapest discriminator + result.

---

## H1–H8 (falsified)
- attacker_tier: public mempool — discriminators do not require ordering or capital.
- result: no exploit.

## H9 — AMMWrapper subsidy reserve drain via validated relayer

| Constraint | Value |
|---|---|
| attacker_tier | requires registered relayer EOA (privileged) |
| ordering | none (subsidy applied per-trade) |
| oracle | none |
| liquidity | requires user-signed orders that produce shortfall on the chosen path |
| capital | none beyond gas |

Per-trade extractable: `makerAssetAmount × subsidyFactor / 10000`.

At AMMWrapper balance ≈ 7.6 WETH + 51K USDT + 153K DAI + 1.9K USDC, total
~$190K, so even an unbounded number of trades would exhaust the reserves
before any single trade extracted material value.  If `subsidyFactor = 100bp`
(1%), draining $190K requires ~$19M of trade flow whose AMM leg
underperforms by exactly 1%.  Permission gate (operator-controlled
relayer set) breaks this — not E3.

## Open follow-up — 0x v4 OtcOrders / RfqOrders

Different protocol (`0xDef1C0ded9bec7F1a1670819833240f027b25EfF`).  Worth
its own engagement.  History of RFQ-flow bugs disclosed (e.g., expiry
nonce-bucket manipulation).  Use this engagement's framework as template:
- enumerate signing fields per order type
- map `_collect`-equivalent permit/permit2 sources
- check replay store and per-feature domain separators
- audit Settler routing if integrated.
