# Hugging Face Setup Guide

This guide explains how to set up Hugging Face authentication for dataset recording and uploading.

## Why Hugging Face?

When you record episodes with `lerobot-record`, the data is automatically uploaded to Hugging Face Hub. This allows you to:
- Store datasets in the cloud
- Share datasets with others
- Access datasets from any machine
- Version control your datasets
- Train models using cloud-hosted data

## Prerequisites

You need a Hugging Face account. If you don't have one:
1. Go to https://huggingface.co/join
2. Create a free account
3. Verify your email

## Step 1: Get Your Access Token

1. Go to https://huggingface.co/settings/tokens
2. Click "New token"
3. Give it a name (e.g., "mortis-dataset")
4. Select permissions:
   - ✅ **Write** (required for uploading datasets)
   - ✅ Read (optional but recommended)
5. Click "Generate token"
6. **Copy the token** (you won't be able to see it again!)

## Step 2: Login with CLI

Run the login command:

```bash
huggingface-cli login
```

When prompted, paste your token and press Enter.

**Example:**
```
Token: hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Add token as git credential? (Y/n) Y
Token is valid (permission: write).
Your token has been saved to /home/user/.cache/huggingface/token
Login successful
```

## Step 3: Verify Authentication

Check that you're logged in:

```bash
huggingface-cli whoami
```

You should see your username and email.

## Step 4: Configure HF_USER

Add your Hugging Face username to `.env`:

```bash
echo "HF_USER=your-username" >> .env
```

Replace `your-username` with your actual Hugging Face username (shown by `whoami`).

## Complete Setup Flow

```bash
# 1. Install dependencies
make install

# 2. Login to Hugging Face
huggingface-cli login
# Paste your token when prompted

# 3. Verify login
huggingface-cli whoami

# 4. Add username to .env
echo "HF_USER=your-username" >> .env

# 5. Setup dataset infrastructure
make setup-dataset

# 6. Start recording!
cd data/mortis_manipulation/scripts
./record_task_0.sh
```

## Troubleshooting

### "Command not found: huggingface-cli"

The CLI is installed with the `huggingface_hub` package, which is included in the project dependencies.

```bash
# Reinstall dependencies
make install

# Or install manually
pip install huggingface_hub[cli]
```

### "Invalid token"

Your token may have expired or been revoked:
1. Go to https://huggingface.co/settings/tokens
2. Delete the old token
3. Create a new token with **write** permissions
4. Run `huggingface-cli login` again with the new token

### "Permission denied" when uploading

Your token needs **write** permissions:
1. Go to https://huggingface.co/settings/tokens
2. Check your token's permissions
3. If it doesn't have write access, create a new token with write permissions
4. Login again with the new token

### Token stored in wrong location

The token is stored in `~/.cache/huggingface/token` by default. If you're having issues:

```bash
# Check if token file exists
ls -la ~/.cache/huggingface/token

# Remove old token
rm ~/.cache/huggingface/token

# Login again
huggingface-cli login
```

### Multiple accounts

If you have multiple Hugging Face accounts:

```bash
# Logout from current account
huggingface-cli logout

# Login with different account
huggingface-cli login
```

## Security Best Practices

✅ **DO**:
- Keep your token secret (never commit to git)
- Use tokens with minimal required permissions
- Revoke tokens you're not using
- Use different tokens for different projects

❌ **DON'T**:
- Share your token with others
- Commit tokens to version control
- Use tokens with more permissions than needed
- Reuse the same token everywhere

## Token Permissions Explained

- **Read**: Download public and private datasets/models
- **Write**: Upload datasets and models, create repositories
- **Admin**: Manage organization settings (not needed for Mortis)

For Mortis dataset recording, you need **Write** permission.

## Where is Data Uploaded?

When you record episodes, they're uploaded to:
```
https://huggingface.co/datasets/{HF_USER}/mortis_manipulation
```

For example, if your username is `john-doe`:
```
https://huggingface.co/datasets/john-doe/mortis_manipulation
```

You can view, manage, and share your dataset from this URL.

## Dataset Privacy

By default, datasets are **public**. To make them private:

1. Go to your dataset page: `https://huggingface.co/datasets/{HF_USER}/mortis_manipulation`
2. Click "Settings"
3. Under "Visibility", select "Private"
4. Click "Update settings"

**Note**: Private datasets require a Pro account or are limited in size on free accounts.

## Next Steps

After authentication is set up:
1. ✅ You're ready to record episodes
2. ✅ Data will automatically upload to Hugging Face
3. ✅ You can train models using your dataset
4. ✅ You can share your dataset with others

See [RECORDING_GUIDE.md](RECORDING_GUIDE.md) for recording instructions.

## Additional Resources

- Hugging Face Hub Documentation: https://huggingface.co/docs/hub
- Hugging Face CLI Documentation: https://huggingface.co/docs/huggingface_hub/guides/cli
- LeRobot Documentation: https://github.com/huggingface/lerobot
- Token Management: https://huggingface.co/settings/tokens
