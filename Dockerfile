FROM python:3.11-slim

# ── Install Node.js 20 + browser dependencies ──────────────────────
RUN apt-get update && apt-get install -y curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get install -y \
       libnss3 libatk-bridge2.0-0 libdrm2 libxcomposite1 \
       libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 \
       libasound2 libatspi2.0-0 libgtk-3-0 libx11-xcb1 \
       fonts-liberation xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python dependencies ────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Node dependencies ──────────────────────────────────────────────
COPY package.json package-lock.json ./
RUN npm ci

# ── Cypress browser (Electron) ────────────────────────────────────
RUN npx cypress install

# ── Playwright browser (Chromium) ─────────────────────────────────
RUN npx playwright install chromium --with-deps

# ── Copy project files ─────────────────────────────────────────────
COPY . .

# ── Default entrypoint ─────────────────────────────────────────────
ENTRYPOINT ["python", "qa_automation.py"]
