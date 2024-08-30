# This is a copy of the dockerfile that I use for the backend
# Use an official Python 3 runtime as a parent image
FROM python:3.9

# Install ping, iproute2, and vim
RUN apt-get update && apt-get install -y \
    iputils-ping \
    iproute2 \
    vim \
    curl \
    tmux

# Copy the .tmux.conf file to the home directory of the container
COPY .tmux.conf /root/.tmux.conf

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

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app

