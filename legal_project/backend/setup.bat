@echo off
echo.
echo ====================================
echo  Legal Backend Setup Script (Windows)
echo ====================================
echo.

echo [1/4] Installing dependencies...
echo.
call npm install

if %errorlevel% neq 0 (
  echo ERROR: npm install failed
  pause
  exit /b 1
)

echo.
echo [2/4] Dependencies installed successfully!
echo.

echo [3/4] Creating .env file...
if exist .env (
  echo .env file already exists - skipping
) else (
  echo MONGODB_URI=mongodb://localhost:27017/legal-database > .env
  echo PORT=5000 >> .env
  echo NODE_ENV=development >> .env
  echo JWT_SECRET=your_jwt_secret_key_here_change_in_production >> .env
  echo FRONTEND_URL=http://localhost:3001 >> .env
  echo .env file created!
)

echo.
echo [4/4] Setup Complete!
echo.
echo ====================================
echo  Next Steps:
echo ====================================
echo.
echo 1. Make sure MongoDB is installed and running:
echo    - Download: https://www.mongodb.com/try/download/community
echo    - After install, run mongod in Command Prompt
echo.
echo 2. Start the backend server:
echo    npm run dev
echo.
echo 3. Backend will run on: http://localhost:5000
echo.
echo 4. Frontend will connect automatically
echo.
pause
