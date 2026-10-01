FROM python:3.12-slim

# Split into two layers: the NodeSource bootstrap + nodejs package produce a
# large layer, and keeping it separate keeps each pushed blob small enough for
# the registry's size limit.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# The sidecar is invoked via `npx @earendil-works/pi-coding-agent`, which uses
# this global install; the previous per-directory install duplicated it.
RUN npm install -g @earendil-works/pi-coding-agent

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
