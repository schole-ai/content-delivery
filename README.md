# Bloom Tutor

## Overview

Bloom Tutor is a platform designed to facilitate the generation, evaluation, and delivery of educational content using Bloom's Taxonomy, RAG, and advanced LLM models. It supports functionalities such as question generation, knowledge graph management, and interactive user interfaces for learning.

## Features

- **AI Question Generation**: Generate questions based on Bloom's Taxonomy.
- **Knowledge Graph Integration**: Manage and query knowledge graphs for enhanced content delivery.
- **Interactive Frontend**: A React-based interface for seamless user interaction.
- **Backend Services**: Python-based backend for processing and data management.

---

## Local Setup Instructions

### Prerequisites

- Node.js (v16 or higher)
- Python (v3.8 or higher)
- Docker & Docker Compose
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

5. Build and run using Docker locally:

   ```bash
   docker compose up --build
   ```

6. Access the application at:
   - Frontend: [http://localhost:5173](http://localhost:5173)
   - Backend: [http://localhost:8009](http://localhost:8009)

---

## 🖥️ Deployment on Google Cloud VM with Docker + Artifact Registry

This section explains how to deploy the platform on a Google Cloud Virtual Machine using Docker images stored in **Artifact Registry**.

### ✅ Prerequisites

- You have a VM instance running on Google Cloud.
- You are the owner of the GCP project (e.g. `schole-edtech`).
- Docker is installed on the VM.
- You have pushed your images to Artifact Registry (steps below).

---

### 🔧 Step 1 – Create Artifact Registry (only once)

```bash
gcloud artifacts repositories create content-delivery   --repository-format=docker   --location=us   --description="Docker repo for backend and frontend"
```

---

### 🐳 Step 2 – Tag and Push Docker Images (from your local machine)

```bash
# Authenticate Docker with Artifact Registry
gcloud auth configure-docker us-docker.pkg.dev

# Tag images
docker tag content-delivery-backend us-docker.pkg.dev/schole-edtech/content-delivery/content-delivery-backend:latest
docker tag content-delivery-frontend us-docker.pkg.dev/schole-edtech/content-delivery/content-delivery-frontend:latest

# Push images
docker push us-docker.pkg.dev/schole-edtech/content-delivery/content-delivery-backend:latest
docker push us-docker.pkg.dev/schole-edtech/content-delivery/content-delivery-frontend:latest
```

---

### ☁️ Step 3 – Connect to the VM and Setup Docker

```bash
# Connect to your VM
gcloud compute ssh your-vm-name --zone=us-central1-a

# Install Docker (if not already installed)
sudo apt update
sudo apt install docker.io -y
sudo usermod -aG docker $USER
newgrp docker

# Authenticate Docker inside the VM
gcloud auth configure-docker us-docker.pkg.dev
```

---

### 📦 Step 4 – Prepare Production Docker Compose File

Create a file named `docker-compose.prod.yml` on the VM with the following content:

```yaml
version: "3.8"

services:
  backend:
    image: us-docker.pkg.dev/schole-edtech/content-delivery/content-delivery-backend:latest
    ports:
      - "8009:8009"
    env_file:
      - .env
    restart: always

  frontend:
    image: us-docker.pkg.dev/schole-edtech/content-delivery/content-delivery-frontend:latest
    ports:
      - "5173:5173"
    env_file:
      - .env
    restart: always
```

> Make sure to copy your `.env` file to the same directory on the VM.

---

### 🚀 Step 5 – Run the containers on your VM

```bash
docker compose -f docker-compose.prod.yml up -d
```

You can now access the application from the **public IP** of your VM:

- Frontend: `http://<VM-IP>:5173`
- Backend: `http://<VM-IP>:8009`

---

### 🌐 Enable Public Access (Frontend & Backend)

By default, Google Cloud blocks all incoming traffic. To make your app accessible from the internet, open the necessary ports via firewall rules (from your local machine not connected to ssh, not from the server):

### ✅ Frontend (port 5173)

```bash
gcloud compute firewall-rules create allow-content-delivery-frontend \
  --allow=tcp:5173 \
  --target-tags=http-server \
  --description="Allow access to content-delivery frontend on port 5173" \
  --direction=INGRESS \
  --priority=1000 \
  --network=default
```

### ✅ Backend (port 8009)

```bash
gcloud compute firewall-rules create allow-content-delivery-backend \
  --allow=tcp:8009 \
  --target-tags=http-server \
  --description="Allow access to content-delivery backend on port 8009" \
  --direction=INGRESS \
  --priority=1000 \
  --network=default
```

> Make sure your VM has the tag `http-server`, or these rules will not apply.

### 🔁 Optional: Auto-start on VM reboot

To ensure the containers restart automatically when the VM reboots:

1. Edit your crontab:

   ```bash
   crontab -e
   ```

2. Add this line at the end:
   ```bash
   @reboot docker compose -f /path/to/docker-compose.prod.yml up -d
   ```

---

## 🧪 Example: Pull and Run a Single Container (for testing)

If you only want to test the backend image:

```bash
docker pull us-docker.pkg.dev/schole-edtech/content-delivery/content-delivery-backend:latest
docker run -p 8009:8009 --env-file .env us-docker.pkg.dev/schole-edtech/content-delivery/content-delivery-backend:latest
```

---

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.
