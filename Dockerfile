FROM python:3.12-slim

ARG RELEASE_TAG=v4.1.0
LABEL org.opencontainers.image.version=$RELEASE_TAG

# ── Install Node.js 22 + browser dependencies for Cypress, Playwright, and WebdriverIO ──
RUN apt-get update && apt-get install -y curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && apt-get install -y \
         chromium chromium-driver \
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
RUN npm ci --include=dev

# ── Cypress browser (Electron) ────────────────────────────────────
RUN npx cypress install

# ── Playwright browser (Chromium) ─────────────────────────────────
RUN npx playwright install chromium --with-deps

# ── Copy project files ─────────────────────────────────────────────
COPY . .

# ── Default entrypoint ─────────────────────────────────────────────
ENTRYPOINT ["python", "qa_automation.py"]
