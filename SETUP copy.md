# Quick Setup Guide

## 🚀 Fast Setup (5 minutes)

### Step 1: Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=medicapsoia
JWT_SECRET_KEY=dev-secret-key-change-in-production
EOF

# Run backend
uvicorn server:app --reload
```

Backend will run on: **http://localhost:8000**

### Step 2: Frontend Setup

```bash
# Navigate to frontend (in a new terminal)
cd frontend

# Install dependencies
npm install
# OR
yarn install

# Create .env file for local development
echo "REACT_APP_API_URL=http://localhost:8000" > .env

# Run frontend
npm start
# OR
yarn start
```

Frontend will run on: **http://localhost:3000**

## ✅ Verify Setup

1. Open http://localhost:3000 in your browser
2. You should see the OIA website homepage
3. Check http://localhost:8000/docs for API documentation

## 🔧 MongoDB Setup Options

### Option A: Local MongoDB (Recommended for Development)

```bash
# macOS (using Homebrew)
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Linux (Ubuntu/Debian)
sudo apt-get install mongodb
sudo systemctl start mongod

# Windows
# Download and install from: https://www.mongodb.com/try/download/community
```

### Option B: MongoDB Atlas (Cloud - Free Tier Available)

1. Go to https://www.mongodb.com/cloud/atlas
2. Create free account
3. Create a cluster
4. Get connection string
5. Update `backend/.env`:
   ```
   MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
   ```

## 🐛 Common Issues

### Backend won't start
- Check MongoDB is running: `mongosh` or `mongo`
- Verify `.env` file exists in `backend/` directory
- Check port 8000 is not in use

### Frontend can't connect to backend
- Ensure backend is running on port 8000
- Check `REACT_APP_API_URL` in `frontend/.env` is `http://localhost:8000`
- Check browser console for CORS errors (backend should handle this)

### Port already in use
```bash
# Backend - use different port
uvicorn server:app --reload --port 8001

# Frontend - use different port
PORT=3001 npm start
```

## 📝 Next Steps

1. Visit http://localhost:3000/admin to access admin dashboard
2. Default credentials may be in database seeding script
3. Explore API docs at http://localhost:8000/docs
4. Start adding content through the admin panel!

