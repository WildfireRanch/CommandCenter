# CommandCenter Frontend

Next.js 14 frontend for CommandCenter energy management system.

## 🎯 Features

- **Home Dashboard** - System overview with real-time stats
- **Energy Monitoring** - Battery SOC, solar production (coming soon)
- **Agent Chat** - AI-powered solar controller (coming soon)
- **Real-time Updates** - Live data from Railway API

## 🚀 Quick Start

### Local Development

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env.local
   # Edit .env.local if needed (defaults to https://api.wildfireranch.us)
   ```

3. **Run development server**:
   ```bash
   npm run dev
   ```

4. **Open**: http://localhost:3000

### Build for Production

```bash
npm run build
npm start
```

## 🔧 Environment Variables

Create `.env.local` with:

```env
NEXT_PUBLIC_API_URL=https://api.wildfireranch.us
```

**For Vercel deployment**, set in dashboard:
- `NEXT_PUBLIC_API_URL` = `https://api.wildfireranch.us`

## 📦 Vercel Deployment

### Automatic (Git Push)

1. **Connect Repository** to Vercel
2. **Root Directory**: `vercel/`
3. **Environment Variables**: Set `NEXT_PUBLIC_API_URL`
4. **Deploy!**

### Manual (CLI)

```bash
npm install -g vercel
cd /path/to/CommandCenter/vercel
vercel
```

## 🏗️ Architecture

```
Next.js Frontend (Vercel)
    ↓ HTTPS
Railway API (FastAPI)
    ↓
PostgreSQL + TimescaleDB
```

## 📂 Project Structure

```
vercel/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Home page
│   │   ├── globals.css         # Global styles
│   │   ├── dashboard/          # Energy dashboard (TODO)
│   │   └── chat/               # Agent chat (TODO)
│   ├── components/             # Reusable components
│   └── lib/                    # Utilities
├── public/                     # Static assets
├── package.json
├── next.config.js
├── tailwind.config.js
└── tsconfig.json
```

## 🎨 Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Charts**: Recharts (for energy dashboard)
- **HTTP**: Axios

## 🔄 API Integration

The frontend connects to your Railway API:

**Base URL**: `https://api.wildfireranch.us`

**Endpoints used**:
- `GET /health` - System health check
- `GET /energy/latest` - Latest energy snapshot
- `GET /energy/stats?hours=24` - Historical data (coming soon)
- `POST /agent/ask` - Chat with agent (coming soon)

## 📊 Current Pages

### Home (`/`)
- System health indicator
- Real-time battery SOC
- Real-time solar production
- Quick action cards
- Links to dashboard and chat

### Coming Soon
- `/dashboard` - Full energy monitoring with charts
- `/chat` - Agent interaction interface
- `/logs` - Activity viewer

## 🐛 Troubleshooting

### Build Fails

```bash
# Clear cache and rebuild
rm -rf .next
npm run build
```

### API Connection Issues

1. Check Railway API is running: `curl https://api.wildfireranch.us/health`
2. Verify `NEXT_PUBLIC_API_URL` is set correctly
3. Check browser console for CORS errors

### Vercel Deployment Errors

**"Root Directory not found"**:
- Ensure Vercel project settings has `Root Directory` = `vercel/`

**"No Next.js version detected"**:
- ✅ FIXED - `package.json` now includes `next` dependency

**Build timeout**:
- Check `package.json` scripts are correct
- Ensure dependencies are listed properly

## 🔐 Security

- All API keys in environment variables (never in code)
- CORS handled by Railway API
- HTTPS enforced by Vercel

## 📝 Development Notes

### Adding New Pages

1. Create file in `src/app/your-page/page.tsx`
2. Next.js automatically creates the route
3. Use `'use client'` for client-side rendering
4. Import from `@/components` for shared components

### Fetching Data

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL
const response = await fetch(`${API_URL}/your-endpoint`)
const data = await response.json()
```

### Styling

Use Tailwind utility classes:
```tsx
<div className="bg-white rounded-lg shadow p-6">
  {/* Your content */}
</div>
```

## 🎯 Roadmap

- [x] Basic home page with live data
- [ ] Energy dashboard with charts
- [ ] Agent chat interface
- [ ] Activity logs viewer
- [ ] User authentication
- [ ] Dark mode
- [ ] Mobile optimization
- [ ] PWA support

## 🔗 Related Projects

- **Railway API**: `/railway/` - FastAPI backend
- **MCP Server**: `/mcp-server/` - Claude Desktop integration
- **Dashboards**: `/dashboards/` - Streamlit ops dashboards
- **CrewAI Studio**: `/crewai-studio/` - Agent management GUI

## 📞 Support

**Issues**: Check main CommandCenter repository
**Logs**: Vercel dashboard → Deployments → View Logs
**Monitoring**: Vercel analytics automatically enabled

---

Built for Wildfire Ranch | CommandCenter v1.0
