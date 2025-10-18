FROM docker.io/ctfd/ctfd:3.8.0

USER root

COPY ./auth-oidc /opt/CTFd/CTFd/plugins/auth_oidc
COPY ./requirements.txt /opt/CTFd

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

