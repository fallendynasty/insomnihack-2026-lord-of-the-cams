import hashlib

# --- Values from your Packet ---
USERNAME = "Sauron"
REALM = "Mordor"
NONCE = "bb22cafe02"
URI = "/h265Preview_01_main"
METHOD = "DESCRIBE"
TARGET_HASH = "79c1aeea6c111489072db68fcb791a2d"

# --- Wordlist Configuration ---
WORDLIST_PATH = "rockyou.txt"

def crack():
    # Pre-calculate HA2 since it doesn't change with the password
    ha2_input = f"{METHOD}:{URI}"
    ha2 = hashlib.md5(ha2_input.encode()).hexdigest()
    
    print(f"[*] Starting crack against response: {TARGET_HASH}")
    print(f"[*] HA2 calculated: {ha2}")
    
    try:
        # Use latin-1 because rockyou.txt often contains non-utf8 characters
        with open(WORDLIST_PATH, 'r', encoding='latin-1') as f:
            for line in f:
                password = line.strip()
                
                # Step 1: Calculate HA1
                ha1_input = f"{USERNAME}:{REALM}:{password}"
                ha1 = hashlib.md5(ha1_input.encode()).hexdigest()
                
                # Step 2: Calculate final response
                final_input = f"{ha1}:{NONCE}:{ha2}"
                final_hash = hashlib.md5(final_input.encode()).hexdigest()
                
                # Step 3: Compare
                if final_hash == TARGET_HASH:
                    print("\n" + "="*30)
                    print(f"[!] PASSWORD FOUND: {password}")
                    print("="*30)
                    return
                    
    except FileNotFoundError:
        print(f"[!] Error: {WORDLIST_PATH} not found.")

if __name__ == "__main__":
    crack()