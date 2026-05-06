#!/bin/bash
# DataVint Quick Deploy Script

set -e  # Exit on error

echo "🚀 DataVint Deployment Script"
echo "=============================="
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ] && [ ! -d "client" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

# 1. Build frontend
echo "📦 Building frontend..."
cd client
npm install
npm run build
cd ..
echo "✅ Frontend built successfully"
echo ""

# 2. Test backend locally
echo "🧪 Testing backend..."
cd server
python3 -c "import fastapi, uvicorn, pandas, numpy; print('All dependencies OK')"
cd ..
echo "✅ Backend dependencies verified"
echo ""

# 3. Ready to deploy
echo "✨ Build complete! Ready to deploy."
echo ""
echo "Next steps:"
echo "1. Deploy backend to Railway: https://railway.app"
echo "2. Deploy frontend to Vercel: cd client && vercel --prod"
echo "3. Configure your domain DNS settings"
echo ""
echo "📖 Full guide: See DEPLOYMENT.md"
