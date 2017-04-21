FROM python:alpine
RUN mkdir -p /opt/leanix_admin
RUN mkdir -p /opt/models/
COPY . /opt/leanix_admin
WORKDIR /opt/leanix_admin
RUN pip install --no-cache-dir -r requirements.txt
WORKDIR /opt/models

ENV LX_MTM_BASE_URL="https://local-svc.leanix.net/services/mtm/v1"
ENV LX_ADMIN_BASE_URL="https://local-eam.leanix.net/beta/api/v1"

ENTRYPOINT [ "/usr/local/bin/leanix-admin" ]