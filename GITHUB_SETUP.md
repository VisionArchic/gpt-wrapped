# 🔧 GitHub Setup & Deployment - Manual Guide

## Problem: Can't Push to GitHub

GitHub no longer accepts passwords. You need a **Personal Access Token (PAT)**.

## Solution: Two Options

### Option A: Use Personal Access Token (Recommended)

#### Step 1: Create GitHub Token

1. Go to GitHub.com and sign in
2. Click your profile picture (top right) → **Settings**
3. Scroll down → Click **Developer settings** (bottom left)
4. Click **Personal access tokens** → **Tokens (classic)**
5. Click **Generate new token** → **Generate new token (classic)**
6. Settings:
   - **Note**: `GPT Wrapped Deployment`
   - **Expiration**: 90 days (or No expiration)
   - **Scopes**: Check `repo` (full control of private repositories)
7. Click **Generate token**
8. **COPY THE TOKEN NOW** - you can't see it again!
   - It looks like: `ghp_abc123xyz...`

#### Step 2: Create Repository on GitHub

1. Go to github.com
2. Click **+** (top right) → **New repository**
3. Repository name: `gpt-wrapped`
4. Description: `ChatGPT conversation analytics dashboard`
5. Choose **Public** or **Private**
6. **Don't** initialize with README/license/gitignore (we already have them)
7. Click **Create repository**

#### Step 3: Fix Remote URL and Push

```bash
cd /Users/visionarchic/Documents/python/antigravity

# Remove the old remote (with placeholder URL)
git remote remove origin

# Add correct remote (replace YOUR_USERNAME with your actual username)
git remote add origin https://github.com/visionarchic/gpt-wrapped.git

# Add ALL files
git add .

# Commit
git commit -m "Initial commit: GPT Wrapped with backend"

# Push (it will ask for credentials)
git push -u origin main
```

When prompted:
- **Username**: `visionarchic`
- **Password**: Paste your Personal Access Token (the `ghp_...` one)

---

### Option B: Use SSH Keys (More Secure, No Passwords)

#### Step 1: Generate SSH Key

```bash
# Check if you already have SSH keys
ls -al ~/.ssh

# If you see id_rsa.pub or id_ed25519.pub, you already have a key!
# Otherwise, generate one:
ssh-keygen -t ed25519 -C "anupam99911@gmail.com"

# Press Enter for all prompts (use default location)
```

#### Step 2: Add SSH Key to GitHub

```bash
# Copy your public key
cat ~/.ssh/id_ed25519.pub
# Or if you have RSA:
# cat ~/.ssh/id_rsa.pub
```

1. Copy the entire output (starts with `ssh-ed25519` or `ssh-rsa`)
2. Go to GitHub.com → Settings → **SSH and GPG keys**
3. Click **New SSH key**
4. Title: `MacBook Air`
5. Paste the key
6. Click **Add SSH key**

#### Step 3: Use SSH Remote URL

```bash
cd /Users/visionarchic/Documents/python/antigravity

# Remove old remote
git remote remove origin

# Add SSH remote
git remote add origin git@github.com:visionarchic/gpt-wrapped.git

# Add and commit
git add .
git commit -m "Initial commit: GPT Wrapped with backend"

# Push (no password needed!)
git push -u origin main
```

---

## Quick Fix Commands (Copy & Paste)

**Using Token (Easier):**
```bash
cd /Users/visionarchic/Documents/python/antigravity
git remote remove origin
git remote add origin https://github.com/visionarchic/gpt-wrapped.git
git add .
git commit -m "Initial commit: GPT Wrapped with backend"
git push -u origin main
# Enter: visionarchic
# Enter: [paste your GitHub token]
```

**Using SSH (More secure):**
```bash
cd /Users/visionarchic/Documents/python/antigravity
ssh-keygen -t ed25519 -C "anupam99911@gmail.com"
cat ~/.ssh/id_ed25519.pub
# Copy output and add to GitHub → Settings → SSH keys
git remote remove origin
git remote add origin git@github.com:visionarchic/gpt-wrapped.git
git add .
git commit -m "Initial commit: GPT Wrapped with backend"
git push -u origin main
```

---

## After Successful Push

1. ✅ Go to https://github.com/visionarchic/gpt-wrapped
2. ✅ You should see all your files!
3. ✅ Continue with deployment to Render.com and Streamlit Cloud

---

## Common Errors

**"remote origin already exists"**
```bash
git remote remove origin
# Then add it again
```

**"repository not found"**
- Make sure you created the repo on GitHub first
- Check the repository name matches exactly

**"Permission denied (publickey)"** (SSH only)
```bash
# Test SSH connection
ssh -T git@github.com
# Should say: "Hi username! You've successfully authenticated"
```

---

## What's Next?

After pushing to GitHub:

1. **Deploy Backend** → Render.com (free)
2. **Deploy Frontend** → Streamlit Cloud (free)
3. **Setup Gmail** → App password for emails

Full guide: `FULL_DEPLOYMENT.md`
