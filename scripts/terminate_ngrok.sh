#!/bin/bash

# Load environment variables from .env file
if [ -f ".env" ]; then
    export $(cat .env | xargs)
fi

# Check if NGROK_AUTH_TOKEN is set
if [ -z "$NGROK_AUTH_TOKEN" ]; then
    echo "Error: NGROK_AUTH_TOKEN is not set. Please set it in the .env file."
    exit 1
fi

# Function to terminate existing ngrok sessions
terminate_ngrok_sessions() {
    headers="Authorization: Bearer $NGROK_AUTH_TOKEN"
    api_url="https://api.ngrok.com/tunnel_sessions"
    
    # Get the list of active sessions
    response=$(curl -s -H "$headers" -H "Ngrok-Version: 2" "$api_url")
    
    # Check if the response contains sessions
    if echo "$response" | grep -q '"tunnel_sessions":'; then
        # Extract session IDs
        session_ids=$(echo "$response" | grep -o '"id":"[^"]*' | sed 's/"id":"//')
        
        # Terminate each session
        for session_id in $session_ids; do
            delete_url="$api_url/$session_id"
            delete_response=$(curl -s -X DELETE -H "$headers" -H "Ngrok-Version: 2" "$delete_url")
            echo "Terminated ngrok session: $session_id"
        done
    else
        echo "No active ngrok sessions found."
    fi
}

# Terminate existing ngrok sessions
terminate_ngrok_sessions