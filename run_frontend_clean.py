import subprocess
import sys
import os
import shutil

frontend_dir = r"e:\UMT\FYP\Ultimate final version for FYP-1\khizer fyp\khizer fyp\serenemind\frontend"
node_path = r"C:\Users\DELL\Downloads\node-portable\node-v20.11.1-win-x64"

os.chdir(frontend_dir)

# Clean build cache
print("🧹 Cleaning build cache...")
if os.path.exists(os.path.join(frontend_dir, ".next")):
    shutil.rmtree(os.path.join(frontend_dir, ".next"))
print("✅ Cache cleared")

# Set environment
env = os.environ.copy()
env["NODE_PATH"] = node_path
env["PATH"] = f"{node_path};{env.get('PATH', '')}"

# Run next dev
print("\n🚀 Starting Next.js dev server...")
print("📍 URL: http://localhost:3000\n")

cmd = [os.path.join(node_path, "npm.cmd"), "run", "dev"]

try:
    subprocess.run(cmd, env=env, cwd=frontend_dir, shell=True)
except KeyboardInterrupt:
    print("\n\n⛔ Server stopped")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
