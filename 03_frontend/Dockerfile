FROM node:20-alpine

WORKDIR /app

# Accept build arguments for white-label configuration
ARG VITE_API_URL
ARG VITE_API_KEY
ARG VITE_APP_NAME

# Set as environment variables for the build process
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_API_KEY=$VITE_API_KEY
ENV VITE_APP_NAME=$VITE_APP_NAME

# Copy package files
COPY 03_frontend/package*.json ./
# Remove lockfile to regenerate with correct platform dependencies (fixes Rollup native module issue)
RUN rm -f package-lock.json && npm install

# Copy source and build
COPY 03_frontend/ .
RUN npm run build

EXPOSE 3000

# Use Vite's preview server
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]
