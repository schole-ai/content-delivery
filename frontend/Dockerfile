FROM node:18-slim

WORKDIR /app

COPY package*.json ./
RUN npm install --include=dev

COPY . .

RUN npm run build

EXPOSE 5173

CMD ["npm", "run", "dev"]