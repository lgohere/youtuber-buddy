# Build stage
FROM node:18-alpine AS build-stage

WORKDIR /app

# Accept build arguments
ARG VITE_API_URL=http://localhost:8000/api
ENV VITE_API_URL=$VITE_API_URL

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy configuration files and root HTML
COPY index.html .
COPY vite.config.js .
COPY tailwind.config.js .
COPY .eslintrc.js .

# Copy source code
COPY src/ ./src/

# Build for production
RUN npm run build

# Production stage
FROM nginx:alpine AS production-stage

# Install curl for health checks
RUN apk add --no-cache curl

# Copy built files
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"] 