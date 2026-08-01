FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY dds_analyst_prompt.md .

CMD ["npx", "@earendil-works/pi-coding-agent", "--mode", "rpc", "--no-session"]
