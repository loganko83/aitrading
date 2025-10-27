module.exports = {
  apps: [{
    name: "trading-backend",
    script: "venv/bin/uvicorn",
    args: "main:app --host 0.0.0.0 --port 8001",
    cwd: "/mnt/storage/trading/trading-backend",
    interpreter: "none",
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: "500M",
    env: {
      DATABASE_URL: "postgresql://tradingbot:tradingbot_secure_password_2025@localhost:5432/trading_bot",
      ENVIRONMENT: "development"
    },
    error_file: "/mnt/storage/trading/trading-backend/logs/pm2-error.log",
    out_file: "/mnt/storage/trading/trading-backend/logs/pm2-out.log",
    log_date_format: "YYYY-MM-DD HH:mm:ss Z"
  }]
};
