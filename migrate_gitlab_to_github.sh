#!/bin/bash

# Script: migrate_gitlab_to_github.sh
# Purpose: Automate migration of a local git repo (e.g., cloned from GitLab) to a new GitHub repo.
#          Ensures all history, tags, AND foreign remote branches are pushed.
# Note: Use within the folder you want to migrate, must run git init if .git folder doesnt exist

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <NEW_GITHUB_URL> [REMOTE_NAME]"
    echo "Example: $0 https://github.com/username/repo.git github"
    exit 1
fi

GITHUB_URL="$1"
REMOTE_NAME="${2:-github}" # Default to 'github' if not provided
OLD_ORIGIN="origin"

echo "=== Starting Migration to $GITHUB_URL as remote '$REMOTE_NAME' ==="

# 1. Add Remote
if git remote | grep -q "^$REMOTE_NAME$"; then
    echo "Remote '$REMOTE_NAME' already exists. Skipping add."
else
    echo "Adding remote '$REMOTE_NAME'..."
    git remote add "$REMOTE_NAME" "$GITHUB_URL"
    echo "Remote added."
fi

# 1.5 Handle Uncommitted Changes
if [ -n "$(git status --porcelain)" ]; then
    echo "=== Detected uncommitted changes ==="
    BACKUP_BRANCH="migration-backup-$(date +%Y%m%d-%H%M%S)"
    echo "Creating backup branch: $BACKUP_BRANCH"
    git checkout -b "$BACKUP_BRANCH"
    git add .
    git commit -m "Backup of uncommitted changes during migration"
    echo "Uncommitted changes saved to $BACKUP_BRANCH"
else
    echo "Working directory clean. No backup branch needed."
fi

# 2. Push Mirror (Pushes local branches and tags)
echo "=== Step 1: Pushing Mirror (Local Branches & Tags) ==="
git push --mirror "$REMOTE_NAME"

# 3. Push Remote Branches (The Critical Fix)
# If the local repo was just a clone, it might not have local branches for every remote branch.
# 'git push --mirror' only pushes what is local. We need to explicitly push origin/* to target/*
echo "=== Step 2: Pushing All Remote-Tracking Branches ==="

# Check if origin exists
if git remote | grep -q "^$OLD_ORIGIN$"; then
    echo "Detected '$OLD_ORIGIN'. Pushing refs/remotes/$OLD_ORIGIN/* to refs/heads/* on $REMOTE_NAME..."
    
    # We use a refspec to map all remote branches from origin directly to heads on the new remote
    git push "$REMOTE_NAME" "refs/remotes/$OLD_ORIGIN/*:refs/heads/*"
else
    echo "Warning: Remote '$OLD_ORIGIN' not found. Skipping remote branch push."
fi

echo "=== Migration Complete! ==="
echo "Verify at: $GITHUB_URL"
echo "To rename remotes locally, run:"
echo "  git remote rename $OLD_ORIGIN gitlab_old"
echo "  git remote rename $REMOTE_NAME origin"
