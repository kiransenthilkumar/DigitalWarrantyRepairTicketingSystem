# Render Deployment Checklist

Your app is **ready** for Render with persistent file storage. Follow these steps:

## Before Deploying

### 1. Database Setup
- [ ] Create a PostgreSQL database on Render (free tier available)
- [ ] Copy the connection string (format: `postgresql://user:password@host/database`)

### 2. Environment Variables (Set in Render Dashboard)
Set these in your Render service's Environment tab:

```
FLASK_ENV=production
SECRET_KEY=<generate-a-secure-random-key-here>
DATABASE_URL=<your-postgresql-connection-string>
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=<your-email>
MAIL_PASSWORD=<your-app-password>
```

**Important:** 
- Generate a strong SECRET_KEY (e.g., using `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- Use real email credentials or leave MAIL_* blank if not needed
- Never commit `.env` with real secrets

### 3. File Uploads - NOW PERSISTENT ✅
Your app is configured to use Render's free 512MB persistent disk for file uploads.

**How it works:**
- Uploads are stored at `/var/data/uploads` on Render (1GB persistent disk mounted)
- For local development, uploads go to `static/uploads/` folder
- The app automatically detects the environment and stores accordingly
- A new route `/uploads/<filename>` serves the files

**No additional setup needed** - just deploy!

### 4. Deploy on Render
1. Connect your GitHub repository to Render
2. Create a new "Web Service"
3. Choose deployment method:
   - **Option A (Recommended):** Use `render.yaml` - automatically configures the persistent disk
     - Simply upload the repository with `render.yaml`, Render will auto-detect it
   - **Option B:** Manual configuration
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn app:app`
     - Add Persistent Disk: name "uploads", mount path "/var/data", size 1GB
     - Set environment variables (from step 2)
4. Click Deploy

### 5. Verify Deployment
- [ ] App loads at your Render URL
- [ ] Can log in with admin@example.com / admin123
- [ ] Database migrations work correctly
- [ ] Static files (CSS, JS) load properly
- [ ] Can upload product images and they persist

## After Successful Deployment

### Security Updates Needed:
1. **Change default admin password** in the admin panel
2. **Update SECRET_KEY** periodically
3. **Set up email notifications** properly
4. **Monitor disk usage** - 1GB can store ~5000-10000 typical invoice images

## Disk Usage Guidelines

- Each product image: ~200KB-500KB average
- 1GB persistent disk = ~2000-5000 product images
- If you exceed storage, you can:
  - Upgrade the persistent disk size in Render dashboard
  - Implement image compression
  - Archive old uploads

## Troubleshooting

**"unable to open database file"**
- Ensure DATABASE_URL is set correctly in Render environment

**"Static files not loading"**
- Whitenoise is configured, should auto-serve static files
- CSS/JS files from `static/` folder are served automatically

**"Port already in use"**
- The app reads PORT from environment, should work automatically

**"502 Bad Gateway"**
- Check Render logs: Dashboard → Your Service → Logs
- Verify all environment variables are set
- Confirm database connection works

**"File uploads not persisting"**
- Check that the persistent disk is mounted at `/var/data`
- Verify disk has available space
- Check Render logs for permission errors

---

**Status:** Ready for deployment ✅ (with Render persistence)

---

Modified files for Render compatibility:
- `app.py` - Reads PORT from environment, serves uploads via `/uploads/` route
- `config.py` - Auto-detects Render storage at `/var/data`
- `routes/customer.py` - Uses persistent storage for uploads
- `requirements.txt` - Added Whitenoise for static file serving
- `extensions.py` - Added Whitenoise integration and proxy header handling
- `runtime.txt` - Specified Python 3.11.7
- `render.yaml` - Auto-configuration for Render deployment with persistent disk


