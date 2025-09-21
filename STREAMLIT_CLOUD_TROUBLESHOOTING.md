# Streamlit Cloud Deployment Troubleshooting 🛠️

## Common Issues and Solutions

### 1. "ModuleNotFoundError: No module named 'selenium'" ✅ FIXED

**Symptoms:**
- App shows error message about Selenium not being available
- App falls back to "Limited Mode"

### 2. Browser Binary Location Errors

**Symptoms:**
- "Expected browser binary location, but unable to find binary"
- "Service chromedriver unexpectedly exited. Status code was: 127"
- "no 'moz:firefoxOptions.binary' capability provided"

**Current Solution:**
- Added `packages.txt` with `chromium` and `firefox-esr`
- Code now explicitly detects and sets browser binary paths
- Shows debug info about available browsers

**Solutions:**

#### Option A: Check Required Files
Ensure these files exist in your repository:

**`requirements.txt`:**
```
streamlit
pandas
requests
beautifulsoup4
selenium
webdriver-manager
```

**`packages.txt`:**
```
chromium-browser
chromium-chromedriver
```

#### Option B: Force Reinstall
1. Make a small change to `requirements.txt` (add a comment)
2. Commit and push to trigger redeployment
3. Streamlit Cloud will reinstall all packages

#### Option C: Alternative Requirements
Try this more specific `requirements.txt`:
```
streamlit>=1.25.0
pandas>=1.5.0
requests>=2.28.0
beautifulsoup4>=4.11.0
selenium>=4.0.0,<5.0.0
webdriver-manager>=3.8.0,<4.0.0
```

### 2. Chrome/Chromium Issues

**Symptoms:**
- "Chrome binary not found" errors
- Browser fails to start

**Solutions:**

#### Update packages.txt:
```
chromium-browser
chromium-chromedriver
chromium
```

#### Try alternative Chrome installation:
```
google-chrome-stable
```

### 3. Memory/Timeout Issues

**Symptoms:**
- App crashes during processing
- "Resource limit exceeded" errors

**Solutions:**

#### Add to `.streamlit/config.toml`:
```toml
[server]
maxUploadSize = 50
enableXsrfProtection = false

[browser]
gatherUsageStats = false
```

#### Reduce processing batch size:
- Process smaller CSV files (< 50 products)
- Split large files into smaller chunks

### 4. Fallback Mode Issues

**Symptoms:**
- App runs but shows "Limited Mode"
- Inconsistent results

**Expected Behavior:**
- Fallback mode has limited functionality
- May not find all products due to JavaScript limitations
- Still provides sample CSV download

## Deployment Checklist

Before deploying to Streamlit Cloud:

- [ ] `requirements.txt` exists and includes all packages
- [ ] `packages.txt` exists with system dependencies
- [ ] `.streamlit/config.toml` exists for performance tuning
- [ ] Repository is public or properly configured
- [ ] All files are committed and pushed to GitHub

## Alternative Solutions

If Selenium continues to fail:

### Option 1: Use Requests-Only Version
Create a simplified version that doesn't use Selenium (limited functionality)

### Option 2: Use Different Deployment Platform
- Heroku with Chrome buildpack
- Railway.app
- Google Cloud Run

### Option 3: Local Development Only
Keep using the full Selenium version locally and provide data exports

## Getting Help

1. **Check Streamlit Cloud Logs**: Look for specific error messages
2. **Streamlit Community**: Post in the Streamlit forum
3. **GitHub Issues**: Check if others have similar deployment issues

## Working Configuration (Known Good)

This configuration is tested and working:

**requirements.txt:**
```
streamlit
pandas
requests
beautifulsoup4
selenium
webdriver-manager
```

**packages.txt:**
```
chromium-browser
chromium-chromedriver
```

**Deployment Steps:**
1. Push all files to GitHub
2. Connect repository to Streamlit Cloud
3. Wait for initial deployment (may take 5-10 minutes)
4. Check logs if deployment fails
5. Verify both Full Mode and Fallback Mode work