import datetime
import pytz
import hashlib
import json
import os
from django.core.mail import send_mail
from django.conf import settings
from backend.firebase import db
from firebase_admin import firestore

def hash_transaction_data(data: dict) -> str:
    # Convert dict to string and hash it
    data_string = f"{data['user_id']}{data['type']}{data['amount']}{data['timestamp']}{data.get('prev_hash', '')}"
    return hashlib.sha256(data_string.encode()).hexdigest()

def log_transaction(user_id, transaction_type, amount):
    # Define Malaysia timezone
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')

    # Get current time in Malaysia time
    timestamp_dt = datetime.datetime.now(malaysia_tz)
    timestamp_unix = int(timestamp_dt.timestamp())

    user_txn_ref = db.collection('transactions').document(user_id).collection('transaction_log')

    # Get the last transaction (sorted by timestamp descending)
    last_txns = user_txn_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).stream()
    prev_hash = None
    for txn in last_txns:
        prev_hash = txn.to_dict().get("hash")
        break

    transaction_data = {
        'user_id': user_id,
        'type': transaction_type,
        'amount': amount,
        'timestamp': timestamp_dt,
        'prev_hash': prev_hash or '',
    }

    # Generate current hash
    transaction_data['hash'] = hash_transaction_data({
        'user_id': user_id,
        'type': transaction_type,
        'amount': amount,
        'timestamp': timestamp_unix,
        'prev_hash': prev_hash or '',
    })

    # Save it
    txn_ref = user_txn_ref.document(str(timestamp_unix))
    txn_ref.set(transaction_data)

    return timestamp_dt

def verify_transaction_chain(user_id):
    txn_ref = db.collection('transactions').document(user_id).collection('transaction_log')
    txns = list(txn_ref.order_by("timestamp").stream())

    prev_hash = ''
    for txn in txns:
        data = txn.to_dict()

        stored_hash = data['hash']
        data_copy = data.copy()
        del data_copy['hash']
        data_copy['prev_hash'] = prev_hash

        recalculated_hash = hash_transaction_data(data_copy)

        if stored_hash != recalculated_hash:
            # Find which fields were tampered
            differences = {}
            for key in data_copy:
                if key in data and data[key] != data_copy[key]:
                    differences[key] = {
                        "expected": data_copy[key],
                        "found": data[key]
                    }

            return {
                "valid": False,
                "message": f"Tampering detected at timestamp {data['timestamp']}",
                "timestamp": data['timestamp'],
                "differences": differences
            }

        prev_hash = stored_hash

    return {"valid": True, "message": "All transactions valid"}

def send_tamper_alert_email(user_id, timestamp, differences):
    subject = f"[ALERT] Blockchain Tampering Detected for User {user_id}"
    message = (
        f"Tampering detected in user {user_id}'s transaction at {timestamp}.\n\n"
        f"Modified fields:\n{json.dumps(differences, indent=4)}"
    )

    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [os.getenv('ALERT_RECEIVER')],
        fail_silently=False,
    )