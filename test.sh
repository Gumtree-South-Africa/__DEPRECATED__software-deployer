#!/bin/bash
set +e
export PYTHONPATH=`pwd`

tests=(
    "deployerlib/tests/aurora_generator_test.py"
    "deployerlib/tests/auroraint_generator_test.py"
    "deployerlib/tests/createdeploypackagetest.py"
    "deployerlib/tests/deploymonitor_notify_test.py"
    "deployerlib/tests/deploymonitor_upload_test.py"
    "deployerlib/tests/createdeploypackagetest.py"
    "deployerlib/tests/local_createdirectory_test.py"
    "deployerlib/tests/pipeline_upload_test.py"
    "deployerlib/tests/deploymonitor_client_test.py"
)

failure=0
failed_tests=()

for test in ${tests[@]}; do
    echo Testing $test
    python $test
    if [ "$?" -ne "0" ]; then
        failure=1
        failed_tests+=($test)
    fi
done


if [ "$failure" -ne "0" ]; then
    echo ""
    echo "==================="
    echo "-------------------"
    echo "[TESTS FAILED]"
    echo "-------------------"
    echo "There were failures in:"
    for test in ${failed_tests[@]}; do
        echo "     $test"
    done
fi
