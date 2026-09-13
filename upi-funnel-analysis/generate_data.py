import random
import csv
from datetime import datetime, timedelta

random.seed(42)

# ---------- Setup: banks, devices, failure rates ----------
banks = ["SBI", "HDFC", "ICICI", "Axis", "Kotak", "PNB", "BOB", "Yes Bank"]
bank_weights = [0.15, 0.15, 0.15, 0.12, 0.12, 0.11, 0.10, 0.10]

bank_failure_rate = {
    "SBI": 0.05, "HDFC": 0.05, "ICICI": 0.05, "Axis": 0.06,
    "Kotak": 0.06, "PNB": 0.14, "BOB": 0.12, "Yes Bank": 0.08
}

device_os = ["Android", "iOS"]
device_weights = [0.72, 0.28]

peak_hours = [10, 11, 12, 19, 20, 21, 22]

failure_reasons = ["Bank Server Timeout", "Insufficient Balance", "Incorrect PIN",
                    "Network Error", "Daily Limit Exceeded"]
reason_weights = [0.35, 0.20, 0.15, 0.15, 0.15]

# Retry only makes sense for TRANSIENT reasons - low balance/wrong PIN won't
# magically fix itself on retry, but a server timeout or network blip often does
TRANSIENT_REASONS = {"Bank Server Timeout", "Network Error"}

# ---------- NEW: users with signup date, for first-time vs repeat ----------
N_USERS = 12000
users = []
start_date = datetime(2026, 1, 1)
for i in range(N_USERS):
    # signup can be anywhere from 2 years before the transaction window
    # to 170 days INTO it - this way some users are brand new when their
    # transaction happens, not everyone signed up long before day 1
    users.append({
        "user_id": f"U{100000+i}",
        "signup_date": start_date + timedelta(days=random.randint(-730, 170))
    })

# ---------- NEW: transaction type ----------
txn_types = ["P2P", "P2M"]
txn_type_weights = [0.70, 0.30]   # P2P = sending to a person, P2M = paying a merchant

N_TRANSACTIONS = 50000
rows = []

STAGE1_DROPOFF = 0.06
STAGE2_DROPOFF = 0.03
RETRY_PROB = 0.35        # chance a FAILED transaction gets retried at all
MAX_RETRIES = 2

def attempt_transaction(user, bank, device, ts, txn_type, is_retry, retry_num, original_id, txn_counter):
    """Simulates ONE attempt (original or retry) through the funnel. Returns the row + status."""
    hour = ts.hour
    funnel_stage_reached = "SETTLEMENT"
    status = "SUCCESS"
    reason = ""

    if not is_retry and random.random() < STAGE1_DROPOFF:
        funnel_stage_reached = "INITIATION"
        status = "ABANDONED"
        reason = "User exited before request sent"
    elif not is_retry and random.random() < STAGE2_DROPOFF:
        funnel_stage_reached = "BANK_AUTH_STARTED"
        status = "ABANDONED"
        reason = "User exited before entering PIN"
    else:
        fail_prob = bank_failure_rate[bank]
        if hour in peak_hours:
            fail_prob = fail_prob * 1.6
        if is_retry:
            fail_prob = fail_prob * 0.5   # retries succeed more often (transient issues clear up)

        if random.random() < fail_prob:
            funnel_stage_reached = "BANK_AUTH_FAILED"
            status = "FAILED"
            reason = random.choices(failure_reasons, weights=reason_weights)[0]
        else:
            funnel_stage_reached = "SETTLEMENT"
            status = "SUCCESS"

    amount = round(random.lognormvariate(6.5, 1.0), 2)
    amount = min(amount, 100000)

    txn_id = f"T{500000 + txn_counter}"
    days_since_signup = (ts.date() - user["signup_date"].date()).days
    user_type = "First-time" if days_since_signup <= 3 else "Repeat"

    row = {
        "transaction_id": txn_id,
        "original_transaction_id": original_id if is_retry else "",
        "is_retry": is_retry,
        "retry_attempt_number": retry_num,
        "user_id": user["user_id"],
        "user_type": user_type,
        "transaction_type": txn_type,
        "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "bank_name": bank,
        "device_os": device,
        "hour": hour,
        "amount": amount,
        "funnel_stage_reached": funnel_stage_reached,
        "status": status,
        "failure_reason": reason
    }
    return row, status, reason, txn_id


txn_counter = 0
for i in range(N_TRANSACTIONS):
    user = random.choice(users)
    bank = random.choices(banks, weights=bank_weights)[0]
    device = random.choices(device_os, weights=device_weights)[0]
    txn_type = random.choices(txn_types, weights=txn_type_weights)[0]

    day_offset = random.randint(0, 180)
    hour = random.randint(0, 23)
    ts = start_date + timedelta(days=day_offset, hours=hour, minutes=random.randint(0, 59))

    # Original attempt
    row, status, reason, txn_id = attempt_transaction(
        user, bank, device, ts, txn_type, is_retry=False, retry_num=0,
        original_id=None, txn_counter=txn_counter
    )
    rows.append(row)
    txn_counter += 1

    # Retry chain - only if original failed AND reason was transient
    retry_num = 1
    current_status, current_reason = status, reason
    while (current_status == "FAILED" and current_reason in TRANSIENT_REASONS
           and retry_num <= MAX_RETRIES and random.random() < RETRY_PROB):
        retry_ts = ts + timedelta(minutes=random.randint(1, 10) * retry_num)
        retry_row, current_status, current_reason, _ = attempt_transaction(
            user, bank, device, retry_ts, txn_type, is_retry=True, retry_num=retry_num,
            original_id=txn_id, txn_counter=txn_counter
        )
        rows.append(retry_row)
        txn_counter += 1
        retry_num += 1

output_path = "/mnt/user-data/outputs/upi_transactions_v3.csv"
with open(output_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} total rows (including retries) -> {output_path}")

from collections import Counter
print("Status breakdown:", dict(Counter(r["status"] for r in rows)))
print("Retry rows:", sum(1 for r in rows if r["is_retry"]))
print("Transaction type:", dict(Counter(r["transaction_type"] for r in rows)))
print("User type:", dict(Counter(r["user_type"] for r in rows)))
