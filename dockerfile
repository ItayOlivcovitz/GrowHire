# Use the official Selenium standalone Chrome image 
FROM selenium/standalone-chrome:latest

# Set working directory inside the container
WORKDIR /app

# Switch to root user for package installation
USER root

# Install dependencies, including Python and GUI tools
RUN apt-get update && apt-get install -y \
    software-properties-common \
    python3-venv \
    python3-pip \
    libegl1 \
    libopengl0 \
    libgl1-mesa-dev \
    libxkbcommon-x11-0 \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libx11-xcb1 \
    libxcb1 \
    libxcb-util1 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-sync1 \
    libxcb-glx0 \
    libxcb-dri3-0 \
    libxcb-dri2-0 \
    xvfb \
    x11-xkb-utils \
    x11vnc \
    fluxbox \
    novnc \
    websockify \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ✅ Ensure Python is available
RUN which python3

# ✅ Create Python virtual environment
RUN python3 -m venv /app/venv

# ✅ Use the virtual environment for Python
ENV PATH="/app/venv/bin:$PATH"

# ✅ Upgrade pip
RUN /app/venv/bin/python3 -m pip install --no-cache-dir --upgrade pip

# ✅ Install dependencies inside the virtual environment
COPY requirements.txt .  
RUN /app/venv/bin/python3 -m pip install --no-cache-dir -r requirements.txt

# ✅ Create necessary directories
RUN mkdir -p /app/resume

# ✅ Copy `Resume.pdf` into the container
COPY resume/Resume.pdf /app/resume/Resume.pdf

# ✅ Copy the entire project
COPY . . 

# Expose necessary ports
EXPOSE 4444 5900 9222 6080

# Set environment variables
ENV DISPLAY=:99

# ✅ Start GUI-related services properly before running the main Python app
CMD /bin/bash -c " \
    Xvfb :99 -screen 0 1920x1080x24 & \
    sleep 2 && \
    setxkbmap us && \
    fluxbox & \
    x11vnc -forever -display :99 -rfbport 5900 -bg && \
    websockify --web /usr/share/novnc/ --cert=none --ssl-only=false --idle-timeout=120 6080 localhost:5900 & \
    exec /app/venv/bin/python3 main.py"

