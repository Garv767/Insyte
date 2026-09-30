import os
import base64
import zipfile
import io

def encode_wallet():
    wallet_path = "Wallet_INSYTE.zip"
    if not os.path.exists(wallet_path):
        print(f"Error: {wallet_path} not found in current directory.")
        return
    
    # We only need the files required by python-oracledb Thin mode
    required_files = ['ewallet.pem', 'tnsnames.ora', 'sqlnet.ora']
    buf = io.BytesIO()
    
    with zipfile.ZipFile(wallet_path, 'r') as zf_in:
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf_out:
            for f in required_files:
                if f in zf_in.namelist():
                    zf_out.writestr(f, zf_in.read(f))
                else:
                    print(f"Warning: {f} not found in {wallet_path}")
    
    wallet_bytes = buf.getvalue()
    encoded = base64.b64encode(wallet_bytes).decode('utf-8')
    
    with open("wallet_base64.txt", "w") as out_f:
        out_f.write(encoded)
    
    print("=" * 60)
    print(f"SUCCESS: Base64 string written to 'wallet_base64.txt'")
    print(f"Length of the encoded string is just {len(encoded)} characters.")
    print("Open the file, press Ctrl+A to select all, and copy it into Vercel.")
    print("=" * 60)

if __name__ == "__main__":
    encode_wallet()
