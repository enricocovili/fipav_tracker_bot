FROM python:3.13-slim

RUN	apt update && \
    apt install -y openssh-client sshpass

# Set working directory
WORKDIR /app

# Copy uv configuration files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN pip install --upgrade pip && pip install -e .

# Copy the rest of the application code
COPY . .

# Run the application
CMD ["python", "main.py"]
