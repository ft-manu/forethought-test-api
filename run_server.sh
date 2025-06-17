#!/bin/bash
set -e
#set -x  # Uncomment for debug: prints each command as it runs

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "[INFO] Activating virtual environment..."
    source venv/bin/activate
fi

# Install requirements
if [ -f requirements.txt ]; then
    echo "[INFO] Installing dependencies..."
    pip install -r requirements.txt
fi

# Function to find an available port starting from a given port
find_available_port() {
    local port=$1
    while lsof -i :$port > /dev/null 2>&1; do
        echo "[WARN] Port $port is in use, trying next port..."
        port=$((port + 1))
    done
    echo $port
}

# Function to kill processes on a port
kill_port() {
    local port=$1
    lsof -ti :$port | xargs kill -9 2>/dev/null
}

# Function to check if a port is in use
is_port_in_use() {
    local port=$1
    lsof -i :$port > /dev/null 2>&1
}

# Function to check if ngrok is running
is_ngrok_running() {
    curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1
}

# Function to verify ngrok domain
verify_ngrok_domain() {
    local domain="learning-teal-prepared.ngrok-free.app"
    local response=$(curl -s "https://$domain")
    if [[ $response == *"ERR_NGROK_3200"* ]]; then
        return 1
    fi
    return 0
}

# Main logic
PORT=3000
while lsof -i :$PORT > /dev/null 2>&1; do
    echo "[WARN] Port $PORT is in use, trying next port..."
    PORT=$((PORT + 1))
done
export PORT

echo "[INFO] Using port: $PORT"
kill_port $PORT

# Start Gunicorn with the correct syntax
echo "[INFO] Starting Gunicorn server on port $PORT..."
gunicorn --bind 0.0.0.0:$PORT test_api_server:app &
GUNICORN_PID=$!

# Wait for Gunicorn to start
echo "[INFO] Waiting for Gunicorn to start..."
for i in {1..30}; do
    if is_port_in_use $PORT; then
        echo "[INFO] Gunicorn is running on port $PORT"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "[ERROR] Gunicorn failed to start"
        kill $GUNICORN_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Start ngrok
if command -v ngrok > /dev/null; then
    echo "[INFO] Starting ngrok tunnel on port $PORT..."
    # Kill any existing ngrok processes
    pkill ngrok || true
    
    # Start ngrok with specific domain
    ngrok http --domain=learning-teal-prepared.ngrok-free.app $PORT > /dev/null 2>&1 &
    NGROK_PID=$!
    
    # Wait for ngrok to start
    echo "[INFO] Waiting for ngrok to start..."
    for i in {1..30}; do
        if is_ngrok_running; then
            echo "[INFO] ngrok is running"
            # Verify the domain is accessible
            if verify_ngrok_domain; then
                echo "[INFO] ngrok domain is accessible"
                echo "[INFO] API is available at: https://learning-teal-prepared.ngrok-free.app"
                break
            else
                echo "[WARN] ngrok is running but domain is not accessible yet, waiting..."
            fi
        fi
        if [ $i -eq 30 ]; then
            echo "[ERROR] ngrok failed to start or domain is not accessible"
            kill $NGROK_PID 2>/dev/null
            kill $GUNICORN_PID 2>/dev/null
            exit 1
        fi
        sleep 1
    done
else
    echo "[WARN] ngrok not found. Skipping ngrok tunnel."
fi

echo "[INFO] Server is running on port $PORT"
echo "[INFO] Press Ctrl+C to stop the server"

# Handle cleanup on exit
trap 'echo "[INFO] Shutting down..."; kill_port $PORT; kill $GUNICORN_PID 2>/dev/null; kill $NGROK_PID 2>/dev/null; pkill ngrok; exit 0' INT TERM

# Keep the script running
wait $GUNICORN_PID 