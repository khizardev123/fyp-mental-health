import subprocess
import sys
import os
import urllib.request
import zipfile

def download_nodejs():
    """Download portable Node.js"""
    print("🔽 Downloading Node.js...")
    url = "https://nodejs.org/dist/v20.11.1/node-v20.11.1-win-x64.zip"
    zip_path = os.path.join(os.path.expanduser("~"), "Downloads", "node.zip")
    
    try:
        urllib.request.urlretrieve(url, zip_path)
        print(f"✅ Downloaded to {zip_path}")
        return zip_path
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

def extract_nodejs(zip_path):
    """Extract Node.js"""
    print("📦 Extracting Node.js...")
    extract_dir = os.path.join(os.path.expanduser("~"), "Downloads", "node-portable")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print(f"✅ Extracted to {extract_dir}")
        return os.path.join(extract_dir, "node-v20.11.1-win-x64")
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return None

def run_frontend(node_path):
    """Run frontend with Node.js"""
    frontend_dir = r"e:\UMT\FYP\Ultimate final version for FYP-1\khizer fyp\khizer fyp\serenemind\frontend"
    os.chdir(frontend_dir)
    
    node_exe = os.path.join(node_path, "node.exe")
    next_cli = os.path.join(frontend_dir, "node_modules", ".bin", "next")
    
    # Set NODE_PATH
    env = os.environ.copy()
    env["NODE_PATH"] = node_path
    env["PATH"] = f"{node_path};{env.get('PATH', '')}"
    
    print(f"🚀 Starting frontend with {node_exe}")
    
    try:
        # Run next dev
        if os.path.exists(f"{next_cli}.cmd"):
            cmd = ["cmd", "/c", f"{next_cli}.cmd", "dev"]
        else:
            cmd = [node_exe, next_cli, "dev"]
        
        subprocess.run(cmd, env=env, cwd=frontend_dir)
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")

if __name__ == "__main__":
    print("🌐 SereneMind Frontend Setup")
    print("=" * 50)
    
    # Try to download and setup Node.js
    zip_path = download_nodejs()
    if zip_path:
        node_path = extract_nodejs(zip_path)
        if node_path:
            run_frontend(node_path)
        else:
            print("⚠️  Setup cancelled")
            sys.exit(1)
    else:
        print("⚠️  Please install Node.js from https://nodejs.org/")
        sys.exit(1)
