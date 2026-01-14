# Deployment Guide - AI Wine Agent

This guide covers deployment options for the AI Wine Agent web application.

## Table of Contents
1. [Local Development](#local-development)
2. [Production Deployment Options](#production-deployment-options)
3. [Vercel Deployment (Recommended)](#vercel-deployment)
4. [Render Deployment](#render-deployment)
5. [AWS Elastic Beanstalk](#aws-elastic-beanstalk)
6. [Docker Deployment](#docker-deployment)
7. [Environment Variables](#environment-variables)

---

## Local Development

### Prerequisites
- Python 3.9+
- pip
- OpenAI API Key
- Pinecone API Key

### Setup

1. **Install Dependencies**
```bash
cd wine-recommender
pip install -r requirements.txt
```

2. **Set Environment Variables**

Create a `.env` file in the `wine-recommender` directory:
```bash
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here
```

3. **Run the Application**
```bash
# From the wine-recommender directory
python app.py

# Or from the project root
python wine-recommender/app.py
```

The application will be available at http://localhost:5000

---

## Production Deployment Options

### Quick Comparison

| Platform | Difficulty | Cost | Best For |
|----------|-----------|------|----------|
| **Vercel** | Easy | Free tier available | Quick deployment, modern UI |
| **Render** | Easy | Free tier available | Python apps, automatic deploys |
| **Railway** | Easy | Pay-as-you-go | Simple setup, good scaling |
| **Heroku** | Medium | $7/mo minimum | Traditional PaaS |
| **AWS EB** | Hard | Pay-as-you-go | Full control, enterprise |
| **Docker + VPS** | Hard | $5-20/mo | Custom requirements |

---

## Vercel Deployment

Vercel is recommended for its simplicity and performance.

### Step 1: Prepare the Application

1. **Install Vercel CLI**
```bash
npm install -g vercel
```

2. **Create `vercel.json` in project root**
```json
{
  "version": 2,
  "builds": [
    {
      "src": "wine-recommender/app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "wine-recommender/app.py"
    }
  ],
  "env": {
    "FLASK_DEBUG": "False"
  }
}
```

3. **Create `requirements.txt` in project root** (if not already)
```bash
cp wine-recommender/requirements.txt .
```

### Step 2: Deploy

1. **Login to Vercel**
```bash
vercel login
```

2. **Deploy**
```bash
vercel
```

3. **Set Environment Variables**

In the Vercel dashboard:
- Go to Project Settings → Environment Variables
- Add:
  - `OPENAI_API_KEY`
  - `PINECONE_API_KEY`
  - `SECRET_KEY`

4. **Redeploy with Environment Variables**
```bash
vercel --prod
```

Your site will be live at `https://your-project.vercel.app`

---

## Render Deployment

Render is excellent for Python applications with automatic deployments from Git.

### Step 1: Prepare Repository

1. Push your code to GitHub/GitLab
2. Ensure `.env` is in `.gitignore`

### Step 2: Create Web Service

1. Go to https://render.com
2. Click **New +** → **Web Service**
3. Connect your repository
4. Configure:
   - **Name**: ai-wine-agent
   - **Region**: Choose nearest to your users
   - **Branch**: main
   - **Root Directory**: wine-recommender
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

### Step 3: Environment Variables

Add in Render dashboard:
```
OPENAI_API_KEY=your_key
PINECONE_API_KEY=your_key
SECRET_KEY=your_secret
```

### Step 4: Deploy

Click **Create Web Service**. Render will automatically deploy.

Your site will be live at `https://ai-wine-agent.onrender.com`

---

## Railway Deployment

Railway offers simple deployment with good developer experience.

### Step 1: Install Railway CLI

```bash
npm install -g @railway/cli
```

### Step 2: Deploy

1. **Login**
```bash
railway login
```

2. **Initialize Project**
```bash
cd /path/to/wine-ai-chatbot
railway init
```

3. **Link to GitHub** (optional)
```bash
railway link
```

4. **Deploy**
```bash
railway up
```

5. **Set Environment Variables**
```bash
railway variables set OPENAI_API_KEY=your_key
railway variables set PINECONE_API_KEY=your_key
railway variables set SECRET_KEY=your_secret
```

6. **Add Start Command**

Create `Procfile`:
```
web: cd wine-recommender && gunicorn app:app
```

Your site will be live at `https://your-app.railway.app`

---

## AWS Elastic Beanstalk

For enterprise deployments with full AWS integration.

### Prerequisites
- AWS CLI installed
- EB CLI installed
- AWS account

### Step 1: Install EB CLI

```bash
pip install awsebcli
```

### Step 2: Initialize EB Application

```bash
cd wine-recommender
eb init -p python-3.9 wine-agent --region us-west-2
```

### Step 3: Create Application Configuration

Create `.ebextensions/python.config`:
```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: app:app
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: "/var/app/current"
```

### Step 4: Set Environment Variables

```bash
eb setenv OPENAI_API_KEY=your_key PINECONE_API_KEY=your_key SECRET_KEY=your_secret
```

### Step 5: Create and Deploy

```bash
eb create wine-agent-env
eb deploy
```

### Step 6: Open Application

```bash
eb open
```

---

## Docker Deployment

For custom VPS or cloud deployments.

### Step 1: Create Dockerfile

Create `wine-recommender/Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_DEBUG=False

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "--timeout", "60", "app:app"]
```

### Step 2: Create docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: ./wine-recommender
    ports:
      - "5000:5000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - FLASK_DEBUG=False
    restart: unless-stopped
```

### Step 3: Deploy

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Deploying to VPS (DigitalOcean, Linode, etc.)

1. **SSH into server**
```bash
ssh user@your-server-ip
```

2. **Install Docker**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

3. **Clone repository**
```bash
git clone https://github.com/yourusername/wine-ai-chatbot.git
cd wine-ai-chatbot
```

4. **Create .env file**
```bash
nano .env
# Add your environment variables
```

5. **Run with Docker**
```bash
docker-compose up -d
```

6. **Set up Nginx reverse proxy**

Create `/etc/nginx/sites-available/wine-agent`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
ln -s /etc/nginx/sites-available/wine-agent /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

7. **Add SSL with Let's Encrypt**
```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings and chat | `sk-...` |
| `PINECONE_API_KEY` | Pinecone API key for vector search | `pcsk_...` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_DEBUG` | Enable debug mode | `False` |
| `SECRET_KEY` | Flask secret key for sessions | Random |
| `PORT` | Port to run on | `5000` |

---

## Performance Optimization

### Production Settings

1. **Use Gunicorn** (already in requirements.txt)
```bash
gunicorn --workers 4 --threads 2 --timeout 60 app:app
```

Workers formula: `(2 x CPU cores) + 1`

2. **Enable Caching**

Add Redis for caching wine recommendations:
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})
```

3. **CDN for Static Files**

Use Cloudflare or AWS CloudFront for serving CSS/JS/images.

4. **Database Connection Pooling**

If using a database, enable connection pooling.

---

## Monitoring

### Application Monitoring

1. **Sentry for Error Tracking**
```bash
pip install sentry-sdk[flask]
```

Add to `app.py`:
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()]
)
```

2. **New Relic for Performance**
```bash
pip install newrelic
newrelic-admin run-program gunicorn app:app
```

### Logging

Add structured logging:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

---

## SSL Certificate

### Automatic (Recommended)

Most platforms (Vercel, Render, Railway) include free SSL certificates automatically.

### Manual (for VPS)

Use Let's Encrypt:
```bash
certbot --nginx -d your-domain.com
```

---

## Custom Domain

### Vercel
1. Go to Project Settings → Domains
2. Add your domain
3. Update DNS records as shown

### Render
1. Go to Settings → Custom Domains
2. Add domain
3. Update DNS CNAME record

### VPS
1. Point A record to your server IP
2. Configure Nginx as shown above
3. Add SSL with Certbot

---

## Troubleshooting

### Port Already in Use
```bash
lsof -ti:5000 | xargs kill -9
```

### Import Errors
```bash
pip install -r requirements.txt --force-reinstall
```

### API Key Errors
Check `.env` file and ensure variables are set correctly.

### Static Files Not Loading
Verify file paths and Flask static folder configuration.

---

## Cost Estimates

### Free Tier Options
- **Vercel**: Free for hobby projects
- **Render**: Free tier with 750 hours/month
- **Railway**: $5 free credit/month

### Paid Options
- **Heroku**: $7/month (Eco dyno)
- **AWS EB**: ~$20-50/month (t2.micro)
- **DigitalOcean Droplet**: $6-12/month

### API Costs
- **OpenAI**: ~$0.0001 per 1K tokens (text-embedding-3-small)
- **Pinecone**: Free tier (1 index, 5M vectors)

---

## Security Best Practices

1. **Never commit `.env` file**
```bash
echo ".env" >> .gitignore
```

2. **Use strong SECRET_KEY**
```python
import secrets
secrets.token_hex(32)
```

3. **Rate limiting**
```bash
pip install flask-limiter
```

4. **HTTPS only in production**

5. **Input validation** (already implemented with Pydantic)

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/wine-ai-chatbot/issues
- Email: concierge@wineagent.ai

---

**Recommended for Quick Start**: Deploy to **Vercel** or **Render** for fastest deployment with minimal configuration.
