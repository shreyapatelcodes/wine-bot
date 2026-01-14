# Deploy Wine Recommender to Render

This guide will walk you through deploying your wine recommendation engine to Render.

## Prerequisites

Before deploying, ensure you have:
- A GitHub account (to connect your repository)
- A Render account (sign up at https://render.com)
- Your OpenAI API key
- Your Pinecone API key
- Your wine catalog data loaded into Pinecone

## Step 1: Push Your Code to GitHub

1. **Commit all changes** (if not already done):
```bash
git add .
git commit -m "Prepare for Render deployment"
```

2. **Push to GitHub**:
```bash
git push origin main
```

If you haven't set up a GitHub repository yet:
```bash
# Create a new repository on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/wine-ai-chatbot.git
git branch -M main
git push -u origin main
```

## Step 2: Create a New Web Service on Render

1. Go to https://render.com and sign in
2. Click **New +** → **Web Service**
3. Connect your GitHub account if you haven't already
4. Select your `wine-ai-chatbot` repository

## Step 3: Configure Your Web Service

Fill in the following settings:

### Basic Settings
- **Name**: `wine-recommender` (or your preferred name)
- **Region**: Choose the region closest to your users:
  - `Oregon` (US West)
  - `Ohio` (US East)
  - `Frankfurt` (Europe)
  - `Singapore` (Asia)
- **Branch**: `main`
- **Root Directory**: `wine-recommender`

### Build Settings
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 60 app:app`

### Plan
- **Instance Type**: `Free` (for testing) or `Starter` ($7/month for production)
  - Free tier: 750 hours/month, sleeps after 15 minutes of inactivity
  - Starter tier: Always on, better performance

## Step 4: Set Environment Variables

In the Render dashboard, scroll down to **Environment Variables** and add:

| Key | Value | Notes |
|-----|-------|-------|
| `OPENAI_API_KEY` | `sk-...` | Your OpenAI API key |
| `PINECONE_API_KEY` | `pcsk_...` | Your Pinecone API key |
| `SECRET_KEY` | Auto-generated | Click "Generate" for a secure random key |
| `FLASK_DEBUG` | `False` | Disable debug mode in production |
| `PYTHON_VERSION` | `3.9.16` | Python version |

**Important**: Keep "Secret" checkbox checked for API keys!

## Step 5: Deploy

1. Click **Create Web Service**
2. Render will start building and deploying your app
3. You can watch the build logs in real-time
4. Wait for the build to complete (usually 2-5 minutes)

## Step 6: Verify Deployment

Once deployed, your app will be available at:
```
https://wine-recommender.onrender.com
```

Test the deployment:

1. **Visit the homepage**: Open the URL in your browser
2. **Test the health endpoint**:
   ```
   https://wine-recommender.onrender.com/health
   ```
   Should return: `{"status": "healthy"}`

3. **Try a recommendation**: Fill out the form and submit

## Step 7: Configure Custom Domain (Optional)

If you want to use your own domain:

1. Go to **Settings** → **Custom Domains**
2. Click **Add Custom Domain**
3. Enter your domain (e.g., `wine.yourdomain.com`)
4. Add the CNAME record to your DNS provider:
   ```
   CNAME wine wine-recommender.onrender.com
   ```
5. Wait for DNS propagation (5-30 minutes)
6. Render will automatically provision an SSL certificate

## Troubleshooting

### Build Fails

**Problem**: Build fails with dependency errors
**Solution**: Check that all dependencies are in `requirements.txt`
```bash
pip freeze > wine-recommender/requirements.txt
git add wine-recommender/requirements.txt
git commit -m "Update requirements.txt"
git push
```

### App Crashes on Startup

**Problem**: App shows "Service Unavailable"
**Solution**: Check the logs in Render dashboard
- Go to **Logs** tab
- Look for error messages
- Common issues:
  - Missing environment variables
  - Import errors (check file paths)
  - Pinecone connection issues

### Environment Variables Not Working

**Problem**: API keys not being read
**Solution**:
1. Verify environment variables are set in Render dashboard
2. Make sure "Secret" checkbox is checked
3. Restart the service: **Manual Deploy** → **Clear build cache & deploy**

### Static Files Not Loading

**Problem**: CSS/JS files return 404
**Solution**: Verify that the `static` and `templates` directories are in the correct location:
```
wine-recommender/
├── app.py
├── static/
│   ├── css/
│   └── js/
└── templates/
    ├── index.html
    └── results.html
```

### Pinecone Connection Timeout

**Problem**: "Pinecone connection timeout" errors
**Solution**:
1. Verify your Pinecone API key is correct
2. Check that your Pinecone index exists
3. Ensure your Pinecone index has the correct dimension (1536 for text-embedding-3-small)
4. Run the `setup_pinecone.py` script locally to verify data is loaded

### Free Tier App Sleeping

**Problem**: App takes 30+ seconds to respond on first request
**Solution**: This is normal for free tier - the app sleeps after 15 minutes of inactivity
- Upgrade to Starter plan ($7/month) for always-on service
- Or accept the cold start delay for development/testing

## Monitoring Your App

### View Logs
- Go to Render dashboard → **Logs**
- View real-time logs of your application
- Filter by log level (info, warning, error)

### Monitor Performance
- Check **Metrics** tab for:
  - Response times
  - Memory usage
  - CPU usage
  - Request count

### Set Up Alerts
- Go to **Settings** → **Notifications**
- Configure email alerts for:
  - Deploy failures
  - Service health checks failing
  - High error rates

## Updating Your App

Render automatically deploys when you push to GitHub:

```bash
# Make your changes
git add .
git commit -m "Update wine recommendations"
git push origin main

# Render will automatically detect the push and redeploy
```

Manual deploy:
1. Go to Render dashboard
2. Click **Manual Deploy** → **Deploy latest commit**

## Performance Optimization

### For Production Use:

1. **Upgrade to Starter Plan** ($7/month)
   - Always on (no cold starts)
   - Better performance
   - More memory

2. **Increase Workers** (if needed for high traffic)
   Edit start command:
   ```
   gunicorn --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 60 app:app
   ```

3. **Add Caching** (optional)
   - Use Redis for caching wine recommendations
   - Render offers Redis add-on

4. **Enable CDN** (optional)
   - Use Cloudflare for static assets
   - Improves load times globally

## Cost Estimates

### Free Tier
- **Cost**: $0/month
- **Limitations**:
  - 750 hours/month
  - Sleeps after 15 min inactivity
  - Slower performance

### Starter Tier (Recommended for Production)
- **Cost**: $7/month
- **Benefits**:
  - Always on
  - Better performance
  - More memory (512 MB)

### API Costs (Separate)
- **OpenAI**: ~$0.10-0.50 per 1000 requests (embeddings + chat)
- **Pinecone**: Free tier (1 index, 5M vectors, sufficient for most use cases)

## Security Best Practices

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Use environment variables** for all secrets
3. **Enable HTTPS** - Automatic on Render
4. **Rotate API keys** periodically
5. **Monitor logs** for suspicious activity
6. **Set up rate limiting** (optional, via Flask-Limiter)

## Support

If you encounter issues:

1. Check Render's status page: https://status.render.com
2. Review Render docs: https://render.com/docs
3. Check build logs in Render dashboard
4. Verify environment variables are set correctly
5. Test locally first to isolate Render-specific issues

## Next Steps

After successful deployment:

- [ ] Test all functionality
- [ ] Set up custom domain (optional)
- [ ] Configure monitoring/alerts
- [ ] Add rate limiting for API endpoints
- [ ] Set up error tracking (e.g., Sentry)
- [ ] Consider upgrading to Starter plan for production
- [ ] Add analytics to track usage

---

**Your wine recommendation engine is now live!** 🍷

Share your deployment URL and start recommending wines to users.
