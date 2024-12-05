# Hull Chat Application

An AI-powered chatbot built with Ionic React and Modal.com, designed to assist University of Hull students.

## Features

- Real-time AI chat interface
- Dark mode UI
- Mobile-responsive design
- Multi-line message support
- Message reactions and copy functionality

## Tech Stack

- Frontend: Ionic React, TypeScript
- Backend: Modal.com, LLaMA-2
- Deployment: Vercel (frontend), Modal.com (backend)

## Project Structure
```
.
├── .github/
│   └── workflows/
│       └── deploy.yml
├── frontend/
│   └── hullchat/
│       ├── src/
│       ├── public/
│       └── package.json
├── modal-api/
│   ├── simple_llm.py
│   └── test_simple_llm.py
└── README.md
```

## Getting Started

1. Frontend Development:
```bash
cd frontend/hullchat
npm install
npm run dev
```

2. Backend Development:
```bash
cd modal-api
modal deploy simple_llm.py
```

## Deployment

- Frontend is automatically deployed to Vercel via GitHub Actions
- Backend is hosted on Modal.com

## Environment Variables

Required environment variables for frontend:
```
VITE_API_URL=https://hull-chat--example-llm-model-chat.modal.run
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License

