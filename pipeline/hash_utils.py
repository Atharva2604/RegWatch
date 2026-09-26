import hashlib

def compute_hash(content: str) -> str:
    """Returns the SHA-256 hash of a given string."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def demo_hashing():
    original_string = "Regulatory requirement: report within 24 hours."
    original_hash = compute_hash(original_string)
    
    print(f"Original String: '{original_string}'")
    print(f"Original Hash  : {original_hash}")
    
    modified_string = "Regulatory requirement: report within 48 hours."
    modified_hash = compute_hash(modified_string)
    
    print(f"\nModified String: '{modified_string}'")
    print(f"Modified Hash  : {modified_hash}")
    
    print("\nResult:")
    if original_hash != modified_hash:
        print("Even a one-character change produces a completely different hash!")
    else:
        print("Hashes are the same (this shouldn't happen!).")

if __name__ == "__main__":
    demo_hashing()
