# Content Delivery

## Overview

Content Delivery is a platform designed to facilitate the generation, evaluation, and delivery of educational content using advanced AI models. It supports functionalities such as question generation, knowledge graph management, and interactive user interfaces for learning.

## Features

- **AI-Powered Question Generation**: Generate questions based on Bloom's Taxonomy.
- **Knowledge Graph Integration**: Manage and query knowledge graphs for enhanced content delivery.
- **Interactive Frontend**: A React-based interface for seamless user interaction.
- **Backend Services**: Python-based backend for processing and data management.

## Setup Instructions

### Prerequisites

- Node.js (v16 or higher)
- Python (v3.8 or higher)
- Neo4j Database
- OpenAI API Key

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd content-delivery
   ```

2. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

3. Install backend dependencies:
   ```bash
   cd ../backend
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   - Create a `.env` file in both `frontend` and `backend` directories.
   - Add the required variables (e.g., `OPENAI_API_KEY`, Neo4j credentials).

### Running the Application

1. Start the Neo4j database.

2. Run the backend:
   ```bash
   cd backend
   python main.py
   ```

3. Run the frontend:
   ```bash
   cd ../frontend
   npm run dev
   ```

4. Access the application at `http://localhost:3000`.

## Usage

- **Frontend**: Interact with the application to load content, answer questions, and view feedback.
- **Backend**: Use scripts for data processing, question generation, and knowledge graph updates.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.