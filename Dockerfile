# Overpass API from Source
# Developed with Claude Code assistance
# https://github.com/paule76/overpass-api-from-source

FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG OVERPASS_VERSION=latest

RUN apt-get update && apt-get install -y \
    g++ \
    make \
    expat \
    libexpat1-dev \
    zlib1g-dev \
    nginx \
    fcgiwrap \
    spawn-fcgi \
    wget \
    sudo \
    bzip2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp

# Download and extract based on version (latest or specific)
RUN if [ "$OVERPASS_VERSION" = "latest" ]; then \
        wget https://dev.overpass-api.de/releases/osm-3s_latest.tar.gz && \
        tar -xzf osm-3s_latest.tar.gz; \
    else \
        wget https://dev.overpass-api.de/releases/osm-3s_v${OVERPASS_VERSION}.tar.gz && \
        tar -xzf osm-3s_v${OVERPASS_VERSION}.tar.gz; \
    fi && \
    cd osm-3s_v* && \
    ./configure CXXFLAGS="-O2" --prefix=/opt/overpass && \
    make -j$(nproc) && \
    make install && \
    cd / && \
    rm -rf /tmp/*

RUN useradd -m -s /bin/bash overpass && \
    mkdir -p /db /opt/overpass/var && \
    chown -R overpass:overpass /db /opt/overpass/var

COPY nginx.conf /etc/nginx/sites-available/default
COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

EXPOSE 80

WORKDIR /db

CMD ["/usr/local/bin/start.sh"]