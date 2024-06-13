FROM ubuntu

# install required library
RUN apt-get update && \
    apt-get install -y ca-certificates curl build-essential

VOLUME [ "/vpnserver/" ]

# download install file, unzip and make it   
RUN cd / && \
    curl -fsSL https://www.softether-download.com/files/softether/v4.43-9799-beta-2023.08.31-tree/Linux/SoftEther_VPN_Server/64bit_-_Intel_x64_or_AMD64/softether-vpnserver-v4.43-9799-beta-2023.08.31-linux-x64-64bit.tar.gz \
    -o ./vpnserver.tar.gz && \
    tar xzvf ./vpnserver.tar.gz && \
    rm vpnserver.tar.gz && \
    chmod 777 /vpnserver/ && \
    cd vpnserver && \
    make && \
    chmod 600 * && \
    chmod 700 vpncmd && \
    chmod 700 vpnserver


EXPOSE 5555

WORKDIR /vpnserver/

CMD ["sh", "-c", "/vpnserver/vpnserver start && sleep 31536000"]
