FROM debian:unstable-slim

ARG USERNAME=starlette
ARG USER_UID=101
ARG USER_GID=$USER_UID

# Create the user
RUN groupadd --system --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    #
    # [Optional] Add sudo support. Omit if you don't need to install software after connecting.
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoera.d/$USERNAME \
    && savedAptMark="$savedAptMark sudo"

RUN set -eux; \
    apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-dev \
    python3-pip \
    python3-virtualenv \
    sudo \
    python3-click \
    git \
    python3.11-venv \
    libsodium-dev \
    python3 \
    python3-pymongo

USER $USERNAME

RUN set -eux; \
    python3 -m virtualenv /home/$USERNAME/.python; \
    . /home/$USERNAME/.python/bin/activate; \
    python -m pip install --upgrade pip setuptools wheel; 

WORKDIR /app/

RUN set -ex; \
    echo "change_me to update starlette_auth" ; \
    . /home/$USERNAME/.python/bin/activate; \
    git clone https://github.com/accent-starlette/starlette-auth.git; \
    cd starlette-auth; \
    python -m pip install --upgrade -r requirements.txt; \
    cd .. 
    
RUN set -ex; \
    echo "change_me to update starlette-1 like_so..."; \
    git clone https://github.com/nixroxursox/starlette-1.git; \
    cd starlette-1; \
    . /home/$USERNAME/.python/bin/activate; \
    python -m pip install --upgrade -r requirements.txt; \
    sudo apt-get update 
#    && sudo apt-get install -y python3-starlette \
#    python3-uvicorn

WORKDIR /app/website


CMD ["/home/starlette/.python/bin/python", "app.py"]
