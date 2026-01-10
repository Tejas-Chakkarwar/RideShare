import subprocess
import sys
import time

def run_script(script_name):
    print(f"\n{'='*50}")
    print(f"🚀 Running {script_name}...")
    print(f"{'='*50}\n")
    
    start_time = time.time()
    try:
        # Run the script as a subprocess
        result = subprocess.run(
            [sys.executable, f"backend/scripts/{script_name}"],
            capture_output=False, # Let it print to stdout directly
            text=True
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"\n✅ {script_name} passed in {duration:.2f}s")
            return True
        else:
            print(f"\n❌ {script_name} failed with exit code {result.returncode}")
            return False
    except Exception as e:
        print(f"\n❌ Error running {script_name}: {e}")
        return False

def main():
    scripts = [
        "verify_profile.py",
        "verify_ratings.py",
        "verify_ux_features.py"
    ]
    
    print("Starting Full Codebase Verification (Sections 1-12)...")
    
    failed_scripts = []
    
    for script in scripts:
        # Add a sleep between scripts to let rate limits reset (Window is 1 min)
        if script != scripts[0]:
            print("\nCooling down for 60 seconds to reset rate limits...")
            time.sleep(60)
            
        success = run_script(script)
        if not success:
            failed_scripts.append(script)
            # Optional: Stop on first failure? Or run all?
            # Let's stop to be safe.
            print("\n⛔ Verification Aborted due to failure.")
            sys.exit(1)
            
    print(f"\n{'='*50}")
    print("🎉 ALL SYSTEMS OPERATIONS VERIFIED SUCCESSFULLY")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
