if [ ! -f /tmp/healthcheck_passed ]; then
  if curl -fs -c /tmp/cookie.txt \
      -d "username=${QBITTORRENT_USER}&password=${QBITTORRENT_PASS}" \
      http://localhost:8082/api/v2/auth/login | grep -q "Ok."; then
    touch /tmp/healthcheck_passed
    curl -fs -b /tmp/cookie.txt http://localhost:8080/api/v2/auth/logout >/dev/null
    exit 0
  else
    exit 1
  fi
else
  curl -fs http://localhost:8082/ >/dev/null || exit 1
fi