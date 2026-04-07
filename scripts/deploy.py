#!/usr/bin/env python3
"""
deploy.py — saiyo-lp deployment script.

Commits public/lp/{slug}/ to the nippo-sync repo and pushes to Vercel.
Verifies the URL is live before returning.

Usage:
    python3 deploy.py <slug> [--company "株式会社山口建設"]

Always asks for explicit confirmation before pushing unless --yes flag is set.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

import urllib.request
import urllib.error

NIPPO_SYNC_DIR = Path("/home/ubuntu/nippo-sync")
DEPLOY_ROOT = NIPPO_SYNC_DIR / "public" / "lp"
PROD_URL_BASE = "https://nippo-sync.vercel.app/lp"


def run(cmd, cwd=None, check=True):
    """Run a shell command and return its output."""
    result = subprocess.run(
        cmd, cwd=cwd, shell=isinstance(cmd, str),
        capture_output=True, text=True
    )
    if check and result.returncode != 0:
        print(f"ERROR: command failed: {cmd}")
        print(f"  stdout: {result.stdout}")
        print(f"  stderr: {result.stderr}")
        sys.exit(1)
    return result


def check_file_exists(slug: str):
    path = DEPLOY_ROOT / slug / "index.html"
    if not path.exists():
        print(f"ERROR: {path} does not exist. Run generate_lp.py first.")
        sys.exit(1)
    size = path.stat().st_size
    print(f"✓ Found {path} ({size:,} bytes)")


def git_status(slug: str):
    result = run(["git", "status", "--porcelain", f"public/lp/{slug}/"], cwd=NIPPO_SYNC_DIR, check=False)
    return result.stdout.strip()


def git_add_commit_push(slug: str, company: str):
    lp_path = f"public/lp/{slug}/"

    # Stage
    print(f"Staging {lp_path}...")
    run(["git", "add", lp_path], cwd=NIPPO_SYNC_DIR)

    # Check if anything is staged
    result = run(["git", "diff", "--cached", "--stat"], cwd=NIPPO_SYNC_DIR, check=False)
    if not result.stdout.strip():
        print("Nothing to commit. Maybe already up-to-date?")
        return False

    # Commit
    msg = f"feat(lp): {slug} — {company} 採用LP"
    print(f"Committing: {msg}")
    run(["git", "commit", "-m", msg], cwd=NIPPO_SYNC_DIR)

    # Push
    print("Pushing to origin/main...")
    run(["git", "push", "origin", "main"], cwd=NIPPO_SYNC_DIR)
    return True


def verify_live(slug: str, timeout: int = 60):
    """Poll the Vercel URL until it returns 200 or times out."""
    url = f"{PROD_URL_BASE}/{slug}"
    print(f"\nVerifying {url}...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    print(f"✓ Live at {url}")
                    return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"  404 — still building, retrying in 5s...")
                time.sleep(5)
                continue
            print(f"  HTTP error {e.code}, retrying in 5s...")
            time.sleep(5)
        except Exception as e:
            print(f"  Error: {e}, retrying in 5s...")
            time.sleep(5)
    print(f"⚠  URL did not return 200 within {timeout}s. Check Vercel dashboard.")
    return False


def main():
    parser = argparse.ArgumentParser(description="Deploy a saiyo-lp slug to nippo-sync.")
    parser.add_argument("slug", help="LP slug (e.g. 'yamaguchi')")
    parser.add_argument("--company", default="", help="Company name for commit message")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--no-verify", action="store_true", help="Skip post-push URL verification")
    args = parser.parse_args()

    print(f"=== saiyo-lp deploy: {args.slug} ===\n")

    # Pre-flight checks
    check_file_exists(args.slug)

    status = git_status(args.slug)
    if status:
        print(f"Changes to commit:\n{status}\n")
    else:
        print("No changes detected. (Maybe already committed.)\n")

    if not args.yes:
        confirm = input(f"Push to nippo-sync.vercel.app/lp/{args.slug}? [y/N]: ")
        if confirm.lower() not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    # Do the deploy
    pushed = git_add_commit_push(args.slug, args.company or args.slug)

    if not pushed:
        print("\nNothing was deployed.")
        return

    if not args.no_verify:
        verify_live(args.slug)

    print(f"\n=== Done ===")
    print(f"Live URL: {PROD_URL_BASE}/{args.slug}")


if __name__ == "__main__":
    main()
