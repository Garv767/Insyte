import os
import base64

def encode_wallet():
    wallet_path = "Wallet_INSYTE.zip"
    if not os.path.exists(wallet_path):
        print(f"Error: {wallet_path} not found in current directory.")
        return
    
    with open(wallet_path, "rb") as f:
        wallet_bytes = f.read()
    
    encoded = base64.b64encode(wallet_bytes).decode('utf-8')
    print("=" * 50)
    print("Copy the following Base64 string and paste it into Vercel as WALLET_BASE64:")
    print("=" * 50)
    print(encoded)
    print("=" * 50)

if __name__ == "__main__":
    encode_wallet()
