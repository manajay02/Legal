# Frontend - MERN Stack Setup

## Getting Started

### Installation

```bash
cd frontend
npm install
```

### Environment Variables

Create a `.env` file in the frontend directory:

```
REACT_APP_API_URL=http://localhost:5000/api
```

### Running the Development Server

```bash
npm start
```

The application will open at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

## Project Structure

```
frontend/
├── public/                 # Static files
│   └── index.html         # Main HTML file
├── src/
│   ├── components/        # Reusable components
│   │   ├── Header.js      # Navigation header
│   │   └── Header.css
│   ├── pages/             # Page components
│   │   ├── Home.js        # Home page
│   │   ├── Upload.js      # PDF upload page
│   │   ├── Classify.js    # Case classification page
│   │   └── *.css          # Styling for pages
│   ├── services/          # API services
│   │   └── caseService.js # Case API calls
│   ├── App.js             # Main App component
│   ├── App.css
│   ├── index.js           # React entry point
│   └── index.css          # Global styles
├── package.json           # Dependencies and scripts
└── README.md
```

## Available Pages

1. **Home** - Landing page with features overview
2. **Upload** - Upload and extract text from PDF documents
3. **Classify** - Classify legal cases into categories

## Features

- Professional UI with Bootstrap styling
- Responsive design for mobile and desktop
- React Router for navigation
- Axios for API calls
- Real-time file upload and processing
- Case classification with confidence scores

## Technologies Used

- **React** - UI library
- **React Router DOM** - Client-side routing
- **Axios** - HTTP client
- **Bootstrap** - CSS framework
- **CSS3** - Custom styling

## Notes

- Make sure your backend is running on `http://localhost:5000`
- Proxy is configured to forward API calls to the backend
- All API endpoints are defined in `caseService.js`
