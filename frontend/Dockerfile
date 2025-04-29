# Use an official Node.js runtime as a parent image
FROM node:18-slim

# Set the working directory in the container
WORKDIR /app

# Copy the rest of the application code to the container
COPY . .

# Ensure clean install
RUN rm -rf node_modules package-lock.json

# Clean install to avoid optional dependency issues
RUN npm install

# Build the application for production
RUN npm run build

# Expose port 3000 for the frontend
EXPOSE 3000

# Start the application using Vite
CMD ["npm", "run", "dev"]
