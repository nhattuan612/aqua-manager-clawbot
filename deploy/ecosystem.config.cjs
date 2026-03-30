const path = require("path");

const root = path.resolve(__dirname, "..");
const envFile = process.env.AQUA_ENV_FILE || path.join(root, ".env");
const env = {
  AQUA_ENV_FILE: envFile,
};

module.exports = {
  apps: [
    {
      name: process.env.AQUA_APP_NAME || "aqua_manager_clawbot",
      cwd: root,
      script: path.join(root, "deploy", "run-dashboard.sh"),
      interpreter: "none",
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 3000,
      env,
    },
  ],
};
