FROM docker.io/ctfd/ctfd:3.8.1

USER root

COPY ./auth_oidc /opt/CTFd/CTFd/plugins/auth_oidc
COPY ./bws_s3 /opt/CTFd/CTFd/plugins/bws_s3
COPY ./challenge_application /opt/CTFd/CTFd/plugins/challenge_application
COPY ./requirements.txt /opt/CTFd
COPY ./config.ini /opt/CTFd/CTFd

USER ctfd

WORKDIR /opt/CTFd

# Ensure dependencies for CTFd plugins are installed
RUN pip install --no-cache-dir -r requirements.txt \
    && for d in CTFd/plugins/*; do \
        if [ -f "$d/requirements.txt" ]; then \
            pip install --no-cache-dir -r "$d/requirements.txt";\
        fi; \
    done;

EXPOSE 8000

ENTRYPOINT ["/opt/CTFd/docker-entrypoint.sh"]

