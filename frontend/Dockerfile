# build env
FROM node:21.7.1-alpine
RUN npm install -g npm@11.2.0
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . ./
RUN npm run build
CMD ["cp", "-r", "build", "result_build"]
