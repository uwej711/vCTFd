# vCTFD

Customized CTFd (3.8.0), see https://github.com/CTFd/CTFd

## Changes

1. Use Postgresql instead of MySQL
2. Keycloak for SSO, plugin auth_oidc to enable in CTFd
3. BWS (OpenStack & Ceph-RGW) for uploads (plugin bws_s3)
4. ArgoCD plugin generator for challange applications (plugin challenge_application)

## Setup

1. Checkout
2. Copy .env.dist to .env
3. To use BWS S3: get credentials and setup BWS_* variables, set UPLOAD_PROVIDER to "bws"
4. To use Keycloak:
   1. docker compose up
   2. make sure to reach the container via name "sso" (e.g. 127.0.0.1  sso in /etc/hosts)
   3. browse to http://sso:8080 to set up Keycloak and a realm and a client and some uses
   4. setup KEYCLOAK_* variables
   5. Restart ctfd container
5. Browse to localhost:8000 and set up CTFd
