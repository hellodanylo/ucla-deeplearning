#!/usr/bin/env zsh

project_path=${0:a:h:h}
cd $project_path/cdk/report_live_usage

go build -o bootstrap
zip lambda.zip bootstrap
aws lambda update-function-code --function-name report-live-usage --zip-file fileb://$PWD/lambda.zip --no-cli-pager
rm lambda.zip bootstrap