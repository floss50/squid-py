#!/bin/bash

# Run this in the root of the squid-py repo
# (to get paths of ./artifacts and the scripts themselves)
# Set the environment variable export TEST_NILE=1 for testing vs. deployed Nile
# Set the environment variable export TEST_NILE=0 for testing vs. local Spree network
# Default (no environment variable) is Spreej

#usage="$(basename) [-h] -- testing
#
#where:
#    -h  show this help text
#
#Run this in the root of the squid-py repo
#(to get paths of ./artifacts and the scripts themselves)
#Set the environment variable export TEST_NILE=1 for testing vs. deployed Nile
#Set the environment variable export TEST_NILE=0 for testing vs. local Spree network
#Default (no environment variable) is Spree"


#RED='\033[0;31m'
#GREEN='\033[0;32m'
#NC='\033[0m' # No Color

source /home/ubuntu/.local/share/virtualenvs/squid-py-T9JvGpNI/bin/activate

BLUE=$(tput setaf 4)
NC=$(tput sgr0)
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
printf "%40s\n" "${blue}This text is blue${normal}"
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
echo $DIR

let passes=0
let fails=0
let total=0
unset summarystring
summarystring=""

runtest() {
#    conda env list
    SCRIPT_PATH=$1
    SCRIPT_NAME=$2
    printf "\n*********************************************************\n"
    printf " Running test: %s\n" $SCRIPT_NAME
    printf "*********************************************************\n"

    python $SCRIPT_PATH/$SCRIPT_NAME

    exit_status=$?
    if [ $exit_status -eq 0 ]; then
        MESSAGE="Success, (exit code "$exit_status")"
        passes=$((passes + 1))
        total=$((total + 1))
        summarystring="$summarystring${GREEN}     ✔ $SCRIPT_NAME${NC}\n"
        #summarystring="$summarystring${GREEN}     ✔ $SCRIPT_NAME\n"
    else
        MESSAGE="Fail, (exit code $exit_status)"
        fails=$((fails + 1))
        total=$((total + 1))
        summarystring="$summarystring${RED}     ✗ $SCRIPT_NAME${NC}\n"
        #summarystring="$summarystring${RED}     ✗ $SCRIPT_NAME\n"
    fi

    printf "\n********* TEST COMPLETE *********************************\n"
#    printf " $($SCRIPT_NAME) : $($MESSAGE)\n"
    printf " %s : %s\n" "$SCRIPT_NAME" "$MESSAGE"
    printf "*********************************************************\n"
}

runtest $DIR register_asset.py
runtest $DIR resolve_asset.py
runtest $DIR search_assets.py
runtest $DIR sign_agreement.py
runtest $DIR buy_asset.py

SQUID_VERSION=$(pip freeze | grep squid)

printf "\n********* SUMMARY OF %d TESTS ***************************\n" $total 

printf "\n"
printf "%s\n" "     Squid version:"
#printf "%s\n" `$SQUID_VERSION`
echo $SQUID_VERSION
printf "\n"
if [ $TEST_NILE -eq 1 ]; then
    printf "     Summary of %s tests against deployed Nile network \n" $total
else
    printf "     Summary of %s tests against local Spree network \n" $total 
fi

printf "\n"
printf "     %s scripts passed\n" $passes
printf "     %s scripts failed\n" $fails 

printf "\n"

#printf "%s\n" $summarystring
echo -e $summarystring
#printf "%s\n" ${NC}

printf "*********************************************************\n"


printf "Uploading to S3...\n"
DATE=`date +%d-%m-%y-%H-%M-%S`
cp ~/testnile.log "~/${DATE} testnile.log"
aws s3 cp ~/testnile.log s3://integration-testing-001/

