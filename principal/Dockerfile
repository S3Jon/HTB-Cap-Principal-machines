FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    openssh-server \
    curl wget \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install \
    flask \
    cryptography \
    jwcrypto \
    PyJWT

# ─── Create users ───
# svc-deploy: the foothold user
RUN useradd -m -s /bin/bash svc-deploy && echo 'svc-deploy:D3pl0y_$$H_Now42!' | chpasswd
# root flag
RUN echo "HTB{r00t_fl4g_pr1nc1p4l_m4ch1n3}" > /root/root.txt

# ─── SSH config ───
RUN mkdir /var/run/sshd
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
RUN mkdir -p /etc/ssh/sshd_config.d

# ─── Setup SSH CA (vulnerable config) ───
COPY setup_ssh_ca.sh /setup_ssh_ca.sh
RUN chmod +x /setup_ssh_ca.sh && /setup_ssh_ca.sh

# ─── User flag ───
RUN echo "HTB{us3r_fl4g_pr1nc1p4l_m4ch1n3}" > /home/svc-deploy/user.txt \
 && chown svc-deploy:svc-deploy /home/svc-deploy/user.txt

# ─── Web application ───
RUN mkdir -p /app/static/js
COPY app/app.py /app/app.py
COPY app/static/index.html /app/static/index.html
COPY app/static/dashboard.html /app/static/dashboard.html
COPY app/static/js/app.js /app/static/js/app.js

# ─── Entrypoint ───
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 22 8080

CMD ["/entrypoint.sh"]
