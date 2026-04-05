# GitHub Actions Setup Guide

## Problem
The GitHub Action is failing because Twelve Data API keys are not configured.

## Solution

### 1. Get Free Twelve Data API Key
1. Go to https://twelvedata.com/pricing
2. Sign up for a free account (800 requests/day)
3. Get your API key from the dashboard

### 2. Add GitHub Secrets
Go to your repository settings and add these secrets:

1. Navigate to: `https://github.com/YOUR_USERNAME/gold-tracker/settings/secrets/actions`
2. Click "New repository secret"
3. Add these secrets:

   **Required Secrets:**
   - `TWELVE_DATA_API_KEY` - Your Twelve Data API key
   - `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
   - `TELEGRAM_CHAT_ID` - Your Telegram chat ID

   **Optional Secrets:**
   - `ALERT_PRICE_ABOVE` - Alert threshold (e.g., "3000")
   - `ALERT_PRICE_BELOW` - Alert threshold (e.g., "2000")

### 3. Verify Setup
After adding secrets, you can:
- Manually trigger the workflow from the Actions tab
- Or wait for the next scheduled run (every 1 hour)

### 4. Get Telegram Credentials (if needed)
1. Talk to @BotFather on Telegram
2. Create a bot and get the token
3. Talk to @userinfobot to get your chat ID

## Troubleshooting
If the action still fails:
1. Check the Actions logs for detailed error messages
2. Verify API keys are correct and active
3. Ensure you haven't exceeded the free tier limit (800 requests/day)
