# This is a copy of the dockerfile that I use for the backend
# Use an official Python 3 runtime as a parent image
FROM python:3.9

# In dockerfiles we use apt-get to install packages instead of 
# apt because apt-get is more low-level and suitable for scripting

# Install ping, iproute2, and vim
RUN apt-get update && apt-get install -y \
    iputils-ping \
    iproute2 \
    vim \
    curl \
    tmux \
    portaudio19-dev \
    espeak \
    alsa-utils \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the .tmux.conf file to the home directory of the container
COPY .tmux.conf /root/.tmux.conf

# Create a non-root user
ARG USERNAME=henk_docker
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
  && useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME \
  # Create a home directory and a config directory for the user as some programs expect these to exist
  && mkdir /home/$USERNAME/.config && chown $USER_UID:$USER_GID /home/$USERNAME/.config 

# Add the user to the sudo group and allow it to run sudo commands without a password 
# Always run apt-get update because docker will otherwise use a cached version of the package list                                               
RUN apt-get update \
  && apt-get install -y sudo \
  && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME\
  && chmod 0440 /etc/sudoers.d/$USERNAME \
  && rm -rf /var/lib/apt/lists/*

# Append the specified lines to the end of the .bashrc file
RUN echo '_tmux_sessions() {' >> /root/.bashrc && \
    echo '    local cur=${COMP_WORDS[COMP_CWORD]}' >> /root/.bashrc && \
    echo '    local sessions=$(tmux list-sessions -F "#S")' >> /root/.bashrc && \
    echo '    COMPREPLY=( $(compgen -W "${sessions}" -- ${cur}) )' >> /root/.bashrc && \
    echo '}' >> /root/.bashrc && \
    echo '' >> /root/.bashrc && \
    echo 'complete -F _tmux_sessions tmux attach-session -t' >> /root/.bashrc && \
    echo 'complete -F _tmux_sessions tmux switch-client -t' >> /root/.bashrc && \
    echo 'complete -F _tmux_sessions tmux kill-session -t' >> /root/.bashrc

# Libraries for opencv
RUN apt-get update && apt-get install -y \
libgl1 \ 
libgtk2.0-dev \
libgtk-3-dev \
pkg-config \
libgl1-mesa-glx \
libglib2.0-0 \
&& rm -rf /var/lib/apt/lists/*


# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app

# Make the container run as the non-root user
USER $USERNAME
