import os
import sys
import shutil
import subprocess

def build():
    print("==================================================")
    print("STEP 1: Compiling React Frontend (Traffic Control Room)")
    print("==================================================")
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
    result = subprocess.run(["npm", "run", "build"], cwd=frontend_dir, shell=True)
    if result.returncode != 0:
        print("[ERROR] Frontend build failed!")
        sys.exit(1)

    print("\n==================================================")
    print("STEP 2: Bundling UI Assets into backend/app/static")
    print("==================================================")
    dist_dir = os.path.join(frontend_dir, "dist")
    static_dest = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "app", "static"))
    
    if os.path.exists(static_dest):
        shutil.rmtree(static_dest)
    shutil.copytree(dist_dir, static_dest)
    print(f"[OK] Successfully copied static UI files from {dist_dir} to {static_dest}")

    print("\n==================================================")
    print("STEP 3: Building Python Distribution (.tar.gz and .whl)")
    print("==================================================")
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Ensure build is installed
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "build", "twine", "wheel"], cwd=root_dir, check=True)
    
    # Build package
    build_result = subprocess.run([sys.executable, "-m", "build"], cwd=root_dir)
    if build_result.returncode != 0:
        print("[ERROR] Python build failed!")
        sys.exit(1)

    print("\n==================================================")
    print("STEP 4: Validating Artifacts with Twine Check")
    print("==================================================")
    dist_artifacts = os.path.join(root_dir, "dist", "*")
    subprocess.run([sys.executable, "-m", "twine", "check", dist_artifacts], cwd=root_dir, shell=True)

    print("\n[SUCCESS] ai-model-router package successfully built!")
    print(f"Artifacts ready in: {os.path.join(root_dir, 'dist')}")

if __name__ == "__main__":
    build()
