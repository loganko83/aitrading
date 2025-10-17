module.exports = {
  apps: [{
    name: 'trading-frontend',
    script: 'npm',
    args: 'start',
    cwd: 'c:/dev/trading/trading-frontend',
    interpreter: 'none',
    env: {
      NODE_ENV: 'production'
    }
  }]
}
