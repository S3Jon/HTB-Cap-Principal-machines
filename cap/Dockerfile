FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    openssh-server \
    vsftpd \
    tcpdump \
    net-tools \
    iproute2 \
    libcap2-bin \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install flask scapy

# ─── Create user nathan ───
RUN useradd -m -s /bin/bash nathan && echo 'nathan:Buck3tH4TF0RM3!' | chpasswd

# ─── SSH config ───
RUN mkdir /var/run/sshd
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# ─── FTP config ───
RUN echo "local_enable=YES" >> /etc/vsftpd.conf \
 && echo "write_enable=YES" >> /etc/vsftpd.conf \
 && echo "chroot_local_user=NO" >> /etc/vsftpd.conf

# ─── Flags ───
RUN echo "HTB{us3r_fl4g_c4p_m4ch1n3}" > /home/nathan/user.txt \
 && chown nathan:nathan /home/nathan/user.txt
RUN echo "HTB{r00t_fl4g_c4p_m4ch1n3}" > /root/root.txt

# ─── Web application ───
COPY app/app.py /app/app.py

# ─── PCAP generado en BUILD TIME (no en runtime) ───
RUN mkdir -p /pcaps
COPY create_pcap.py /create_pcap.py
RUN python3 /create_pcap.py && ls -la /pcaps/

# ─── cap_setuid vulnerability ───
RUN setcap cap_setuid,cap_net_bind_service+eip /usr/bin/python3.8

# ─── Entrypoint ───
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 21 22 80

CMD ["/entrypoint.sh"]
