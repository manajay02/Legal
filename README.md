# ⚖️ Legal Case Analyzer

A full-stack MERN application for analyzing legal documents and finding similar cases from a comprehensive database.

## 🚀 Features

- **📄 Document Upload** - Upload PDF, DOCX, or TXT legal documents for analysis
- **🔍 Similar Case Finder** - AI-powered similarity matching using Jaccard index algorithm
- **📚 Case Library** - Browse and search through categorized legal cases
- **📊 Case Statistics** - View database statistics and category breakdowns
- **🏷️ Case Classification** - Automatic case type detection
- **➕ Add Cases** - Add new cases to the database

## 📁 Project Structure

```
Legal/
├── legal_project/
│   ├── backend/           # Node.js/Express API server
│   │   ├── server.js      # Main server file
│   │   ├── models/        # MongoDB models
│   │   ├── routes/        # API routes
│   │   └── uploads/       # Temporary file uploads
│   ├── frontend/          # React application
│   │   ├── src/
│   │   │   ├── components/  # Reusable components
│   │   │   └── pages/       # Page components
│   │   └── public/
│   ├── dataset/           # Legal case documents by category
│   └── uploads/           # Uploaded files storage
└── README.md
```

## 🛠️ Tech Stack

- **Frontend**: React.js, React Router, Axios
- **Backend**: Node.js, Express.js
- **Database**: MongoDB
- **File Processing**: pdf-parse, mammoth (DOCX)

## 📋 Prerequisites

- Node.js (v14 or higher)
- MongoDB (running locally or MongoDB Atlas)
- npm or yarn

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/ManaJay02/Legal.git
cd Legal
```

### 2. Install Backend Dependencies
```bash
cd legal_project/backend
npm install
```

### 3. Install Frontend Dependencies
```bash
cd ../frontend
npm install
```

### 4. Configure Environment Variables
Create a `.env` file in the `backend` folder:
```env
MONGODB_URI=mongodb://localhost:27017/legal_db
PORT=5000
```

## 🚀 Running the Application

### Start MongoDB
Make sure MongoDB is running on your system.

### Start Backend Server
```bash
cd legal_project/backend
npm start
```
Backend runs on: `http://localhost:5000`

### Start Frontend Server
```bash
cd legal_project/frontend
npm start
```
Frontend runs on: `http://localhost:3000`

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cases` | Get all cases (with pagination) |
| GET | `/api/cases/stats` | Get database statistics |
| GET | `/api/cases/:id` | Get single case by ID |
| POST | `/api/cases` | Add new case |
| DELETE | `/api/cases/:id` | Delete a case |
| POST | `/api/upload` | Upload and extract text from document |
| POST | `/api/similar` | Find similar cases |

## 📂 Case Categories

The system supports the following case categories:
- Criminal
- Civil
- Drug
- Labour
- Family
- Tax
- Environmental
- Financial
- Asset
- Contempt of Court
- Sexual Cases
- Sports
- Terrorism

## 🔧 Configuration

### Backend Configuration
Edit `backend/.env`:
```env
MONGODB_URI=your_mongodb_connection_string
PORT=5000
```

### Frontend Configuration
The frontend uses a proxy to connect to the backend. This is configured in `frontend/package.json`:
```json
"proxy": "http://localhost:5000"
```

## 📝 Usage

1. **Upload a Document**: Go to "Find Similar Cases" and upload a legal document
2. **View Results**: See matching cases ranked by similarity percentage
3. **Browse Library**: Explore all cases in the database
4. **Add to Library**: Add your uploaded case to the database for future reference

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- **Maneth** - *Initial work*

---

⭐ Star this repository if you find it helpful!

