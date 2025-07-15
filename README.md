Rebuild docker

#Store session so its on difference environment
mkdir -p ~/telegram-session



 # 1. Stop and remove old container (if exists)
docker stop tg-sheets
docker rm tg-sheets

# 2. Rebuild image without cache
docker build --no-cache -t telegram-to-sheets .

# 3. Run container with auto-restart and .env support
docker run -d \
  --name tg-sheets \
  --env-file .env \
  -v "$PWD:/app" \
  -v ~/telegram-session:/app/session \
  --restart always \
  telegram-to-sheets



# If just update env

docker stop tg-sheets
docker rm tg-sheets

docker run -d \
  --name tg-sheets \
  --env-file .env \
  telegram-to-sheets


