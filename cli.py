"""
RAG Testing Pipeline - Simple CLI Tool

A simple command-line interface for testing the RAG Testing Pipeline API.
Requires: pip install requests
"""

import sys
import json
import requests


BASE_URL = "http://localhost:8000"


def pretty_print(response):
    """Pretty print HTTP response."""
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except:
        print(response.text)
    print(f"\nStatus: {response.status_code}")


def health():
    """Check API health."""
    resp = requests.get(f"{BASE_URL}/health")
    pretty_print(resp)


def ingest(url):
    """Ingest a single document from URL."""
    resp = requests.post(
        f"{BASE_URL}/ingest",
        json={"url": url, "profile": "default"}
    )
    pretty_print(resp)


def ringest(url, depth=3, max_pages=50):
    """Recursively ingest documents."""
    resp = requests.post(
        f"{BASE_URL}/ingest",
        json={
            "url": url,
            "depth": depth,
            "max_pages": max_pages,
            "profile": "default"
        }
    )
    pretty_print(resp)


def query(text, top_k=5):
    """Query the knowledge base."""
    resp = requests.post(
        f"{BASE_URL}/query",
        json={
            "query": text,
            "top_k": top_k,
            "profile": "default"
        }
    )
    pretty_print(resp)


def feedback(query_id, score, comment=""):
    """Submit feedback (score 0-10)."""
    payload = {"query_id": query_id, "score": int(score)}
    if comment:
        payload["comment"] = comment
    resp = requests.post(f"{BASE_URL}/feedback", json=payload)
    pretty_print(resp)


def metrics():
    """Get metrics summary."""
    resp = requests.get(f"{BASE_URL}/metrics")
    pretty_print(resp)


def profiles():
    """List configuration profiles."""
    resp = requests.get(f"{BASE_URL}/profiles")
    pretty_print(resp)


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nCommands:")
        print("  health                          - Check API health")
        print("  ingest <url>                    - Ingest single page")
        print("  ringest <url> [depth] [max]     - Recursive crawl (default: depth=3, max=50)")
        print("  query <text> [top_k]            - Query knowledge base (default: top_k=5)")
        print("  feedback <id> <score> [comment] - Submit feedback (score 0-10)")
        print("  metrics                         - View metrics")
        print("  profiles                        - List profiles")
        print("\nExamples:")
        print("  python cli.py health")
        print("  python cli.py ingest https://example.com")
        print("  python cli.py ringest https://docs.python.org/3/ 2 20")
        print('  python cli.py query "How do I use Python?"')
        print("  python cli.py feedback abc-123 8 'Very helpful!'")
        print("  python cli.py metrics")
        return

    cmd = sys.argv[1]

    try:
        if cmd == "health":
            health()
        elif cmd == "ingest":
            if len(sys.argv) < 3:
                print("Usage: ingest <url>")
                return
            ingest(sys.argv[2])
        elif cmd == "ringest":
            if len(sys.argv) < 3:
                print("Usage: ringest <url> [depth] [max_pages]")
                return
            depth = int(sys.argv[3]) if len(sys.argv) > 3 else 3
            max_pages = int(sys.argv[4]) if len(sys.argv) > 4 else 50
            ringest(sys.argv[2], depth, max_pages)
        elif cmd == "query":
            if len(sys.argv) < 3:
                print("Usage: query <text> [top_k]")
                return
            top_k = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            query(sys.argv[2], top_k)
        elif cmd == "feedback":
            if len(sys.argv) < 4:
                print("Usage: feedback <query_id> <score> [comment]")
                return
            comment = sys.argv[4] if len(sys.argv) > 4 else ""
            feedback(sys.argv[2], sys.argv[3], comment)
        elif cmd == "metrics":
            metrics()
        elif cmd == "profiles":
            profiles()
        else:
            print(f"Unknown command: {cmd}")
            print("Run without arguments for help")

    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to {BASE_URL}")
        print("Make sure the API is running: docker-compose up -d")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
