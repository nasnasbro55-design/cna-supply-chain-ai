import subprocess
import sys

def run_pipeline():
    print("=" * 40)
    print("  SUPPLY CHAIN MONITOR - DATA PIPELINE")
    print("=" * 40)
    
    scripts = [
        ("Weather Alerts",    "scripts/fetch_weather.py"),
        ("Gas & Grocery Locations", "scripts/fetch_locations.py"),
        ("Traffic Cameras",   "scripts/fetch_cameras.py"),
        ("Combining Data",    "scripts/combine_data.py"),
    ]
    
    for name, script in scripts:
        print(f"\n⏳ Fetching {name}...")
        result = subprocess.run([sys.executable, script], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {name} done!")
        else:
            print(f"❌ {name} failed:")
            print(result.stderr)
    
    print("\n" + "=" * 40)
    print("  PIPELINE COMPLETE! Data ready for dashboard.")
    print("=" * 40)

run_pipeline()