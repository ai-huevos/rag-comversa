#!/usr/bin/env python
"""
Monitor extraction pipeline progress
"""
import json
import time
from pathlib import Path
from datetime import datetime

PROGRESS_FILE = Path("data/extraction_progress.json")
DB_PATH = Path("data/full_intelligence.db")

def monitor():
    """Monitor extraction progress"""
    print("🔍 Monitoring extraction pipeline...")
    print("=" * 70)
    
    start_time = time.time()
    last_index = 0
    
    while True:
        try:
            # Check progress file
            if PROGRESS_FILE.exists():
                with open(PROGRESS_FILE, 'r') as f:
                    progress = json.load(f)
                
                current_index = progress.get("last_index", 0)
                processed_ids = progress.get("processed_ids", [])
                timestamp = progress.get("timestamp", "")
                
                if current_index != last_index:
                    elapsed = time.time() - start_time
                    rate = current_index / (elapsed / 60) if elapsed > 0 else 0
                    remaining = (44 - current_index) / rate if rate > 0 else 0
                    
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Progress Update:")
                    print(f"  Interviews: {current_index}/44 ({current_index/44*100:.1f}%)")
                    print(f"  Rate: {rate:.1f} interviews/minute")
                    print(f"  Elapsed: {elapsed/60:.1f} minutes")
                    print(f"  Remaining: ~{remaining:.1f} minutes")
                    print(f"  Last update: {timestamp}")
                    
                    last_index = current_index
            
            # Check if complete
            if DB_PATH.exists():
                import sqlite3
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM interviews")
                count = cursor.fetchone()[0]
                conn.close()
                
                if count >= 44:
                    print(f"\n✅ Extraction complete! {count} interviews processed")
                    break
            
            time.sleep(10)  # Check every 10 seconds
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Monitoring stopped")
            break
        except Exception as e:
            print(f"\n⚠️  Error: {str(e)}")
            time.sleep(10)

if __name__ == "__main__":
    monitor()
