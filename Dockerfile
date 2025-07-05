FROM alpine:3.22.0

RUN apk add --no-cache \
    jq \
    bash \
    wget \
    unzip \
    gcompat \
    mpfr-dev \
    webkit2gtk-4.1-dev \
    pcre-dev && \
    wget -O arturo.zip "https://github.com/arturo-lang/nightly/releases/download/2025-07-04/arturo-nightly.2025-07-03-amd64-linux-full.zip" && \
    unzip arturo.zip && \
    mv arturo /usr/local/bin/arturo && \
    chmod +x /usr/local/bin/arturo && \
    rm arturo.zip

RUN arturo --package install unitt 2.0.1

WORKDIR /opt/test-runner
COPY bin/run.sh bin/run.sh
ENTRYPOINT ["/opt/test-runner/bin/run.sh"]
