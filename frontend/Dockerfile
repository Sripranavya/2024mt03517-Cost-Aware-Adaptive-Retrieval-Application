# Frontend image: build with Vite, serve the dev/preview server.
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

# Serve the built assets with Vite preview on 5173.
FROM node:20-alpine AS runtime
WORKDIR /app
COPY --from=build /app/package.json ./
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY --from=build /app/vite.config.ts ./
EXPOSE 5173
CMD ["npm", "run", "preview"]
