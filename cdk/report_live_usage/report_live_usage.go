package main

import (
	"bytes"
	"context"
	_ "embed"
	"fmt"
	"html/template"
	"os"
	"strings"

	collegium "github.com/hellodanylo/collegium"

	"sort"
	"time"

	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/ec2"
	"github.com/aws/aws-sdk-go-v2/service/sagemaker"
	"github.com/aymerick/douceur/inliner"
)

//go:embed report_live_usage.html
var report_live_usage_html string

type UsageLine struct {
	User          string
	Resource      string
	InstanceType  string
	Status        string
	DurationHours float64
	Url           string
}

func sendLiveUsageEmail() {
	usageLines := append(buildEC2UsageLines(), buildSageMakerUsageLines()...)
	if len(usageLines) == 0 {
		return
	}
	fmt.Println(usageLines)

	sort.Slice(usageLines, func(i, j int) bool {
		return usageLines[i].User < usageLines[j].User ||
			usageLines[i].Resource < usageLines[j].Resource ||
			usageLines[i].InstanceType < usageLines[j].InstanceType ||
			usageLines[i].DurationHours < usageLines[j].DurationHours
	})

	teamConfig := collegium.GetTeamConfig()
	htmlBody := formatUsageLines(usageLines, teamConfig.Admin.Name, teamConfig.Admin.Name)
	collegium.SendEmail("UCLA MSBA-434 - AWS Resource Usage", htmlBody, []string{teamConfig.Admin.Email}, teamConfig.Admin.Email)

	linesByUser := make(map[string][]UsageLine)
	for _, usageLine := range usageLines {
		linesByUser[usageLine.User] = append(linesByUser[usageLine.User], usageLine)
	}

	emailByName := make(map[string]string)
	for _, user := range teamConfig.Users {
		emailByName[user.Name] = user.Email
	}

	for user, usageLinesForUser := range linesByUser {
		email, exists := emailByName[user]
		if !exists {
			if user != "" {
				fmt.Printf("Skipping usage line because no user email is associated %v\n", usageLinesForUser)
			}
			continue
		}
		htmlBody := formatUsageLines(usageLinesForUser, teamConfig.Admin.Name, user)
		collegium.SendEmail("UCLA MSBA-434 - AWS Resource Usage", htmlBody, []string{email}, teamConfig.Admin.Email)
	}
}

func buildEC2UsageLines() []UsageLine {
	ec2Svc := ec2.NewFromConfig(collegium.GetSession())
	var usageLines []UsageLine

	result, err := ec2Svc.DescribeInstances(context.TODO(), nil)
	if err != nil {
		fmt.Println("Error describing EC2 instances:", err)
		return usageLines
	}

	for _, res := range result.Reservations {
		for _, instance := range res.Instances {
			if instance.State.Name != "running" {
				continue
			}
			durationHours := time.Since(*instance.LaunchTime).Hours()
			usageLines = append(usageLines, UsageLine{
				User:          "",
				Resource:      "ec2",
				InstanceType:  string(instance.InstanceType),
				Status:        string(instance.State.Name),
				DurationHours: durationHours,
				Url:           fmt.Sprintf("https://%s.console.aws.amazon.com/ec2/home#InstanceDetails:instanceId=%s", os.Getenv("AWS_REGION"), *instance.InstanceId),
			})
		}
	}

	return usageLines
}

func buildSageMakerUsageLines() []UsageLine {
	smSvc := sagemaker.NewFromConfig(collegium.GetSession())
	var usageLines []UsageLine

	result, err := smSvc.ListApps(context.TODO(), &sagemaker.ListAppsInput{MaxResults: aws.Int32(100)})
	if err != nil {
		panic(fmt.Sprintf("Error listing SageMaker apps: %s", err))
	}

	for _, app := range result.Apps {
		if !(app.AppType == "JupyterLab" && (app.Status == "InService" || app.Status == "Pending")) {
			fmt.Printf("Skipping app due to filters %v\n", app)
			continue
		}
		durationHours := time.Since(*app.CreationTime).Hours()
		accountId := collegium.GetAccountId()
		spaceArn := fmt.Sprintf("arn:aws:sagemaker:%s:%s:space/%s/%s", os.Getenv("AWS_REGION"), *accountId, *app.DomainId, *app.SpaceName)

		tags, err := smSvc.ListTags(context.TODO(), &sagemaker.ListTagsInput{ResourceArn: &spaceArn})
		if err != nil {
			fmt.Printf("Failed to get tags for %s due to %s\n", spaceArn, err)
			continue
		}

		var owner *string
		for _, tag := range tags.Tags {
			if *tag.Key == "sagemaker:user-profile-arn" {
				parts := strings.Split(*tag.Value, "/")
				owner = &parts[len(parts)-1]
			}

		}

		if owner == nil {
			fmt.Printf("Skipping app due to unknown owner of the space %v\n", app)
			continue
		}

		usageLines = append(usageLines, UsageLine{
			Resource:      "sagemaker_jupyter",
			InstanceType:  string(app.ResourceSpec.InstanceType),
			User:          *owner,
			Status:        string(app.Status),
			DurationHours: durationHours,
			Url: fmt.Sprintf("https://%s.console.aws.amazon.com/sagemaker/home?region=%s#/studio/%s/user/%s",
				os.Getenv("AWS_REGION"), os.Getenv("AWS_REGION"), *app.DomainId, *owner),
		})
	}

	return usageLines
}

func formatUsageLines(usageLines []UsageLine, from string, to string) string {
	tmpl, _ := template.New("report_live_usage").Parse(report_live_usage_html)
	var buff bytes.Buffer
	tmpl.Execute(&buff, map[string]any{"User": to, "Admin": from, "UsageLines": usageLines})
	html, _ := inliner.Inline(buff.String())
	return html
}

func main() {
	collegium.InitSession()
	if os.Getenv("AWS_LAMBDA_FUNCTION_NAME") != "" {
		lambda.Start(sendLiveUsageEmail)
	} else {
		sendLiveUsageEmail()
	}
}
