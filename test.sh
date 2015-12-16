#!/bin/bash
set +e
export PYTHONPATH=`pwd`

tests=(
    "deployerlib/tests/aurora_generator_test.py"
    "deployerlib/tests/auroraint_generator_test.py"
    "deployerlib/tests/createdeploypackagetest.py"
    "deployerlib/tests/deploymonitor_notify_test.py"
    "deployerlib/tests/deploymonitor_upload_test.py"
    "deployerlib/tests/deploymonitor_createpackage_test.py"
    "deployerlib/tests/createdeploypackagetest.py"
    "deployerlib/tests/local_createdirectory_test.py"
    "deployerlib/tests/pipeline_upload_test.py"
    "deployerlib/tests/deploymonitor_client_test.py"
)

failure=0
failed_tests=()
passed_tests=()

for test in ${tests[@]}; do
    echo Testing $test
    python $test
    if [ "$?" -ne "0" ]; then
        failure=1
        failed_tests+=($test)
    else
        passed_tests+=($test)
    fi
done


echo ""
echo "==================="
echo "-------------------"

for test in ${passed_tests[@]}; do
    echo -e "\033[32mPASS\033[0m  $test"
done

for test in ${failed_tests[@]}; do
    echo -e "\033[31mFAIL\033[0m  $test"
done

echo ""
echo "==================="
echo "-------------------"

if [ "$failure" -ne "0" ]; then
    echo -e "\033[31mTESTS FAILED\033[0m"
    exit 1
else 
    echo -e "\033[32mTESTS PASSED\033[0m"
fi

exit 0
