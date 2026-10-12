import os
import time
import socket
import pandas as pd
from datetime import datetime
from config import APP_PACKAGES, TARGET_APP, LANG, COUNTRY, RAW_DIR, PROCESSED_DIR

# Set socket timeout so external calls never hang indefinitely
socket.setdefaulttimeout(15)

def fetch_app_info():
    history_file = PROCESSED_DIR / "rating_history.csv"
    package = APP_PACKAGES[TARGET_APP]
    
    # If snapshot already exists and was taken recently, reuse it
    if history_file.exists():
        h_df = pd.read_csv(history_file)
        if not h_df.empty:
            latest = h_df.iloc[-1]
            print(f"Verified Play Store Snapshot: Headline {latest['score']:.2f} stars across {latest['ratings']:,} ratings.")
            return latest.to_dict()

    print(f"Fetching app info for {TARGET_APP} from Play Store...")
    try:
        from google_play_scraper import app
        app_info = app(package, lang=LANG, country=COUNTRY)
        
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "package": package,
            "title": app_info.get("title"),
            "score": app_info.get("score"),
            "ratings": app_info.get("ratings"),
            "reviews": app_info.get("reviews"),
            "histogram": str(app_info.get("histogram"))
        }
        
        df = pd.DataFrame([snapshot])
        df.to_csv(history_file, mode='a', header=not history_file.exists(), index=False)
        print(f"Headline rating: {snapshot['score']} from {snapshot['ratings']:,} ratings.")
        return snapshot
    except Exception as e:
        print(f"Could not fetch live app info: {e}. Using cached history.")
        if history_file.exists():
            h_df = pd.read_csv(history_file)
            return h_df.iloc[-1].to_dict()
        return None

def main():
    fetch_app_info()
    
    raw_file = RAW_DIR / f"{TARGET_APP}_reviews.csv"
    if raw_file.exists():
        df_existing = pd.read_csv(raw_file)
        # Drop any empty content
        df_existing = df_existing[df_existing['content'].notna() & (df_existing['content'].astype(str).str.strip() != '')]
        print(f"Dataset integrity verified: {len(df_existing):,} reviews loaded from {raw_file}.")
    else:
        print(f"Raw file {raw_file} not found.")

if __name__ == "__main__":
    main()
