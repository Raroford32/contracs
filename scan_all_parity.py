import json
import subprocess
import time

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
PARITY_ACTIVE_LIB = "273930d21e01ee25e4c219b63259d214872220a2"

def rpc_call(method, params):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    cmd = ["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json", 
           "-d", json.dumps(payload), RPC]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return None

# Load all contracts
with open("contracts.txt", "r") as f:
    contracts = [line.strip() for line in f if line.strip().startswith("0x")]

print(f"Scanning {len(contracts)} contracts for uninitialized Parity wallets...")
print()

vulnerable = []
checked = 0
batch_size = 20  # Check in batches to avoid rate limiting

for i, addr in enumerate(contracts):
    checked += 1
    
    # Get bytecode
    code_resp = rpc_call("eth_getCode", [addr, "latest"])
    if not code_resp or "result" not in code_resp:
        continue
    
    code = code_resp["result"]
    
    # Check if it's a Parity proxy with active library
    if PARITY_ACTIVE_LIB not in code.lower():
        continue
    
    # Check balance
    bal_resp = rpc_call("eth_getBalance", [addr, "latest"])
    if not bal_resp or "result" not in bal_resp:
        continue
    balance_wei = int(bal_resp["result"], 16)
    if balance_wei < 1e17:  # Skip if less than 0.1 ETH
        continue
        
    balance_eth = balance_wei / 1e18
    
    # Check m_numOwners (slot 0)
    storage_resp = rpc_call("eth_getStorageAt", [addr, "0x0", "latest"])
    if not storage_resp or "result" not in storage_resp:
        continue
    m_numOwners = int(storage_resp["result"], 16)
    
    if m_numOwners == 0:
        vulnerable.append((addr, balance_eth))
        print(f"[VULNERABLE] {addr}: {balance_eth:.4f} ETH (m_numOwners=0)")
    
    time.sleep(0.3)  # Rate limit
    
    if checked % 50 == 0:
        print(f"... scanned {checked}/{len(contracts)} contracts")

print()
print("=" * 70)
print(f"TOTAL VULNERABLE WALLETS: {len(vulnerable)}")
total = sum(bal for _, bal in vulnerable)
print(f"TOTAL ETH: {total:.4f}")
print(f"VALUE at $2500/ETH: ${total * 2500:,.2f}")
print("=" * 70)

# Save to file
with open("vulnerable_wallets.json", "w") as f:
    json.dump([{"address": a, "balance_eth": b} for a, b in vulnerable], f, indent=2)

