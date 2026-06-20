#!/usr/bin/env bash
# Pretty, dependency-free status panel for the RDF Differ stack.
# Reads live container state from Docker (truthful — no guessing from compose).
set -uo pipefail

ENV_FILE="${1:-infra/.env}"
# shellcheck disable=SC1090
[ -f "$ENV_FILE" ] && { set -a; . "$ENV_FILE"; set +a; }

ENVIRONMENT="${ENVIRONMENT:-dev}"
SUBDOMAIN="${SUBDOMAIN:-}"
DOMAIN="${DOMAIN:-docker.localhost}"

# Colours (disabled when stdout is not a tty).
if [ -t 1 ]; then
  B=$'\e[1m'; D=$'\e[2m'; G=$'\e[32m'; R=$'\e[31m'; Y=$'\e[33m'; C=$'\e[36m'; X=$'\e[0m'
else
  B=''; D=''; G=''; R=''; Y=''; C=''; X=''
fi

# Each row: container-suffix | label | fallback-access (when no host port is published).
# Traefik serves these over plain http locally (the https-redirect middleware is dropped
# for dev, since ACME can't issue trusted certs for .localhost).
SERVICES=(
  "rdf-differ-api|API|http://api.${SUBDOMAIN}${DOMAIN}"
  "rdf-differ-ui|UI|http://rdf.${SUBDOMAIN}${DOMAIN}"
  "rdf-differ-fuseki|Fuseki|http://fuseki.${SUBDOMAIN}${DOMAIN}"
  "rdf-differ-flower|Flower|http://flower.${SUBDOMAIN}${DOMAIN}"
  "rdf-differ-celery-worker|Celery worker|internal"
  "rdf-differ-redis|Redis|internal"
  "traefik|Traefik|http://monitor.${DOMAIN} (dashboard)"
)

state() { docker inspect -f '{{.State.Status}}' "$1" 2>/dev/null || echo "absent"; }

# First published host port for a container, as http://localhost:<port> — empty if none.
host_url() {
  local p
  p=$(docker port "$1" 2>/dev/null | grep -oE '0\.0\.0\.0:[0-9]+' | head -1 | cut -d: -f2)
  [ -n "$p" ] && printf 'http://localhost:%s' "$p"
}

W_LABEL=14
W_STATUS=9
line() { printf "  ${D}%s${X}\n" "────────────────────────────────────────────────────────────"; }
# Pad by visible length so ANSI colour codes don't break alignment.
pad() { printf "%s%*s" "$1" $(( $2 - ${#1} > 0 ? $2 - ${#1} : 0 )) ""; }

echo
printf "  ${B}${C}RDF Differ${X} ${D}— stack '%s'${X}\n" "$ENVIRONMENT"
line
printf "  ${B}%s %s %s${X}\n" "$(pad SERVICE $W_LABEL)" "$(pad STATUS $W_STATUS)" "ACCESS"
line

for row in "${SERVICES[@]}"; do
  IFS='|' read -r suffix label fallback <<<"$row"
  cname="$suffix"
  # Project services carry the -${ENVIRONMENT} suffix; traefik does not.
  [ "$suffix" != "traefik" ] && cname="${suffix}-${ENVIRONMENT}"

  st=$(state "$cname")
  case "$st" in
    running)  dot="${G}●${X}"; col="$G"; word="running" ;;
    restarting|created) dot="${Y}●${X}"; col="$Y"; word="$st" ;;
    exited|dead) dot="${R}●${X}"; col="$R"; word="$st" ;;
    *) dot="${D}○${X}"; col="$D"; word="—" ;;
  esac

  access="$fallback"
  # Traefik publishes :80/:443 as the proxy entrypoints — not a useful link; keep its
  # dashboard fallback. Everything else: prefer a directly published host port if any.
  [ "$st" = "running" ] && [ "$suffix" != "traefik" ] && { url=$(host_url "$cname"); [ -n "$url" ] && access="$url"; }
  [ "$st" != "running" ] && [ "$st" != "absent" ] && access="${D}(see: docker logs ${cname})${X}"

  printf "  %b %s %b %s\n" "$dot" "$(pad "$label" $W_LABEL)" "${col}$(pad "$word" $W_STATUS)${X}" "$access"
done

line
printf "  ${D}stop: make stop   logs: docker logs <name>   status: make status${X}\n\n"
