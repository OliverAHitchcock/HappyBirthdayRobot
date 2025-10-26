
#!/usr/bin/env bash

# initial command to start with
# cmd="just run-candle-act"
cmd = "echo 'Hello, World!'"

while true; do
    echo ">>> Running: $cmd"
    eval "$cmd"

    echo ">>> Getting next command from Python..."
    next_cmd=$(uv run decide_next.py "$cmd")

    # print what Python returned
    echo ">>> Python suggests: $next_cmd"

    # check if Python says to stop or returns nothing
    if [[ -z "$next_cmd" || "$next_cmd" == "STOP" ]]; then
        echo ">>> Stopping loop."
        break
    fi

    # set up for next iteration
    cmd="$next_cmd"
done
