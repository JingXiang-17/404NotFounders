import os
import shutil
import re
from pathlib import Path

def patch_settings():
    print("Patching apps/api/app/core/settings.py...")
    settings_path = Path("apps/api/app/core/settings.py")
    if not settings_path.exists():
        print("Error: settings.py not found.")
        return

    content = settings_path.read_text(encoding="utf-8")
    
    # Check if demo_mode is already in the dataclass
    if "demo_mode: bool" not in content:
        content = content.replace(
            "model_api_key: str | None = None",
            "model_api_key: str | None = None\n    demo_mode: bool = False"
        )
        
    # Check if demo_mode is passed in the constructor
    if "demo_mode=demo_mode" not in content:
        content = content.replace(
            "model_api_key=_optional_env(\"MODEL_API_KEY\"),",
            "model_api_key=_optional_env(\"MODEL_API_KEY\"),\n            demo_mode=demo_mode,"
        )
        
    settings_path.write_text(content, encoding="utf-8")
    print("settings.py patched successfully.")

def copy_snapshots():
    print("Freezing snapshots...")
    src = Path("data/snapshots")
    dst = Path("data/snapshots_frozen")
    
    if not src.exists():
        print("Error: data/snapshots does not exist. Please run ingestion first.")
        return
        
    if dst.exists():
        print("Removing existing data/snapshots_frozen...")
        shutil.rmtree(dst)
        
    shutil.copytree(src, dst)
    print("Snapshots frozen successfully at data/snapshots_frozen/")

def prepare_demo_quotes():
    print("Preparing demo quotes...")
    src_dir = Path("tests/fixtures/supplier-quotes")
    dst_dir = Path("demo/quotes")
    
    dst_dir.mkdir(parents=True, exist_ok=True)
    
    # Map the existing test fixtures to the demo filenames required by the playbook
    files_to_copy = [
        ("quote_1_cn_sinopoly.pdf", "01_ningbo_usd1180.pdf"),
        ("quote_2_th_siamprime.pdf", "03_thai_usd1210.pdf"),
        ("quote_3_id_nusantara.pdf", "04_chandra_usd1095.pdf"),
    ]
    
    for src_name, dst_name in files_to_copy:
        src_path = src_dir / src_name
        dst_path = dst_dir / dst_name
        if src_path.exists():
            shutil.copy2(src_path, dst_path)
            print(f"Copied {src_name} -> {dst_name}")
        else:
            print(f"Warning: Could not find {src_name}")
            
    print("Demo quotes prepared in demo/quotes/")

def main():
    print("--- LintasNiaga Day 3D Preparation ---")
    patch_settings()
    copy_snapshots()
    prepare_demo_quotes()
    print("--- Done ---")

if __name__ == "__main__":
    main()
