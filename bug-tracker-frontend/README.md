# Bug Tracker Frontend

A modern Next.js frontend for the Bug-to-Task-Graph pipeline, designed to interact with the FastAPI backend.

## Features

- **Bug Management**: Create, view, update, and delete bug reports
- **Attachment Support**: Upload and view multi-modal attachments (images, PDFs, text)
- **Responsive UI**: Modern interface that works well on desktop and mobile
- **TypeScript**: Full type safety throughout the application
- **API Integration**: Seamless integration with the FastAPI backend

## Tech Stack

- **Next.js**: React framework with App Router
- **TypeScript**: For type safety
- **Tailwind CSS**: For styling
- **Axios**: For API calls
- **React Hook Form**: For form handling

## Getting Started

### Prerequisites

- Node.js (v14 or later)
- npm or yarn
- FastAPI backend running on http://localhost:8080

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables (already configured in `.env.local`):
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080
```

### Development

Start the development server:
```bash
npm run dev
```

The application will be available at http://localhost:3000.

### Building for Production

Build the application:
```bash
npm run build
```

Start the production server:
```bash
npm start
```

## Project Structure

```
bug-tracker-frontend/
├── src/
│   ├── app/                 # Next.js app directory (pages)
│   │   ├── bugs/            # Bug-related pages
│   │   │   ├── [id]/        # Bug detail page (dynamic route)
│   │   │   └── create/      # Bug creation page
│   │   ├── globals.css      # Global CSS with Tailwind
│   │   ├── layout.tsx       # Root layout component
│   │   └── page.tsx         # Home page
│   ├── components/          # Reusable components
│   │   ├── ui/              # Generic UI components
│   │   ├── bugs/            # Bug-specific components
│   │   └── attachments/     # Attachment-related components
│   ├── hooks/               # Custom React hooks
│   ├── services/            # API client services
│   └── types/               # TypeScript interfaces
├── .env.local               # Environment variables
├── tailwind.config.js       # Tailwind CSS configuration
├── next.config.js           # Next.js configuration
└── package.json             # Dependencies and scripts
```

## API Integration

The frontend communicates with the FastAPI backend running on http://localhost:8080. The main endpoints used are:

- **Bugs**:
  - `GET /bugs`: Fetch all bugs
  - `GET /bugs/{bug_id}`: Fetch a specific bug
  - `POST /bugs`: Create a new bug
  - `PUT /bugs/{bug_id}`: Update a bug
  - `DELETE /bugs/{bug_id}`: Delete a bug

- **Attachments**:
  - `POST /bugs/{bug_id}/attachments`: Upload an attachment
  - `GET /attachments/{attachment_id}`: Get attachment metadata
  - `GET /attachments/{attachment_id}/content`: Get attachment content

## Future Enhancements

- Authentication and user management
- Real-time updates with WebSockets
- Task graph visualization
- Advanced filtering and searching
- Pagination for large datasets
