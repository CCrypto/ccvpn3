#!/bin/bash

set -e

local_settings="ccvpn/local_settings.py"

run_manage() {
    echo "> manage.py $1..."
    python3 manage.py "$@"
}

run_manage compilemessages
run_manage migrate
run_manage update_stripe_plans

if [ -f $local_settings ] && grep "^STATIC_ROOT" $local_settings; then 
    run_manage collectstatic
fi

