import os
import json
import sqlite3
import urllib.request
import urllib.error

# Configuration
TOKEN = os.environ.get("GITHUB_TOKEN")
USERNAME = "TejasweeSulekh" 
DB_FILE = "traffic.db"

# Include the repositories you want to track
REPOSITORIES = [
    "Odysseus-Agent",
    "blog",
    "tejasweesulekh.github.io",
    "c-elegans-simulator",
    "Fraud-Detection-System"
]

def fetch_data(endpoint):
    url = f"https://api.github.com/repos/{USERNAME}/{endpoint}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    
    # REQUIRED: GitHub API blocks requests without a custom User-Agent
    req.add_header("User-Agent", "project-argus-metrics-collector")
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Failed to fetch {endpoint}: HTTP {e.code}")
        # Print the exact error message from GitHub for easier debugging
        error_body = e.read().decode('utf-8', 'ignore')
        print(f"Error Details: {error_body}")
        return {}
    except Exception as e:
        print(f"Failed to fetch {endpoint}: {e}")
        return {}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Create tables for views and clones
    c.execute('''CREATE TABLE IF NOT EXISTS views
                 (date TEXT, repo TEXT, count INTEGER, uniques INTEGER, PRIMARY KEY(date, repo))''')
    c.execute('''CREATE TABLE IF NOT EXISTS clones
                 (date TEXT, repo TEXT, count INTEGER, uniques INTEGER, PRIMARY KEY(date, repo))''')
    conn.commit()
    return conn

def main():
    if not TOKEN:
        print("Error: GITHUB_TOKEN environment variable is missing.")
        return

    conn = init_db()
    c = conn.cursor()
    
    for repo in REPOSITORIES:
        print(f"Processing {repo}...")
        
        # Fetch and store Views
        views_data = fetch_data(f"{repo}/traffic/views")
        for view in views_data.get("views", []):
            timestamp = view["timestamp"][:10]  # Extract YYYY-MM-DD
            c.execute("INSERT OR REPLACE INTO views (date, repo, count, uniques) VALUES (?, ?, ?, ?)",
                      (timestamp, repo, view["count"], view["uniques"]))
            
        # Fetch and store Clones
        clones_data = fetch_data(f"{repo}/traffic/clones")
        for clone in clones_data.get("clones", []):
            timestamp = clone["timestamp"][:10]
            c.execute("INSERT OR REPLACE INTO clones (date, repo, count, uniques) VALUES (?, ?, ?, ?)",
                      (timestamp, repo, clone["count"], clone["uniques"]))
                      
    conn.commit()
    conn.close()
    print("Database updated successfully.")

if __name__ == "__main__":
    main()