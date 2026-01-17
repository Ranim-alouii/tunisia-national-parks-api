# 🌐 API Keys Setup Guide

## Required API Keys for Tunisia National Parks API

This project uses several external APIs for enhanced functionality. All services offer **FREE** tiers suitable for development and small applications.

---

## 1. 🔑 OpenWeatherMap API (Weather Data)

**Purpose**: Real-time weather and forecasts for parks

**Free Tier**: 1,000 calls/day, 3-hourly forecasts

**Setup Steps**:
1. Visit: https://openweathermap.org/api
2. Sign up for free account
3. Go to "My API keys" in dashboard
4. Copy your API key

**Environment Variable**: `OPENWEATHER_API_KEY`

---

## 2. 📸 Unsplash API (Nature Images)

**Purpose**: High-quality nature and landscape photos for parks

**Free Tier**: 50 requests/hour, 500 requests/month

**Setup Steps**:
1. Visit: https://unsplash.com/developers
2. Create developer account
3. Create new app: "Tunisia Parks"
4. Copy "Access Key" (not Secret Key)

**Environment Variable**: `UNSPLASH_ACCESS_KEY`

---

## 3. 🗺️ Google Places API (Maps & Directions)

**Purpose**: Interactive maps, directions, and place details

**Free Tier**: $200/month credit (enough for 28,000 map loads)

**Setup Steps**:
1. Visit: https://developers.google.com/maps/documentation/places/web-service/get-api-key
2. Create/select Google Cloud project
3. Enable "Places API" and "Maps JavaScript API"
4. Create API key with restrictions if needed

**Environment Variable**: `GOOGLE_PLACES_API_KEY`

---

## 4. 📰 NewsAPI (News & Updates)

**Purpose**: Environmental news and park-related updates

**Free Tier**: 100 requests/day

**Setup Steps**:
1. Visit: https://newsapi.org/register
2. Sign up for free account
3. Verify email
4. Copy your API key from dashboard

**Environment Variable**: `NEWSAPI_API_KEY`

---

## 📝 Environment Setup

1. **Copy the template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** with your actual keys:
   ```env
   OPENWEATHER_API_KEY=your_actual_openweather_key
   UNSPLASH_ACCESS_KEY=your_actual_unsplash_key
   GOOGLE_PLACES_API_KEY=your_actual_google_key
   NEWSAPI_API_KEY=your_actual_newsapi_key
   ```

3. **Restart the server**:
   ```bash
   python main.py
   ```

---

## ✅ Testing API Keys

Run the validation script to check your keys:
```bash
python config_validation.py
```

Expected output:
```
✅ OpenWeather API: Configured
✅ Unsplash API: Configured
✅ Google Places API: Configured
✅ NewsAPI: Configured
```

---

## 🔍 Troubleshooting

### "API key not configured" errors:
- Check `.env` file exists and is readable
- Verify environment variable names match exactly
- Restart server after changing keys

### Rate limit exceeded:
- Most APIs have hourly/daily limits
- Implement caching to reduce API calls
- Consider upgrading to paid tiers for production

### Invalid API key:
- Double-check key was copied correctly
- Ensure no extra spaces or characters
- Verify key is active and not expired

---

## 💰 Cost Estimation (Free Tiers)

| API | Free Limit | Cost if Exceeded |
|-----|------------|------------------|
| OpenWeatherMap | 1,000 calls/day | $0.001/call |
| Unsplash | 500/month | Contact for enterprise |
| Google Maps | $200/month | $0.007/load |
| NewsAPI | 100/day | $449/month |

**Total Monthly Cost**: FREE (within limits)

---

## 🔒 Security Notes

- Never commit `.env` files to version control
- Use API key restrictions when possible
- Rotate keys periodically
- Monitor usage in API dashboards

---

## 📞 Support

If you encounter issues:
1. Check API documentation links above
2. Verify account status on each platform
3. Test keys individually using curl/Postman
4. Check server logs for detailed error messages
