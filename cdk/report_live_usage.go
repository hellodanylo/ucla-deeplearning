package main

import (
	"encoding/json"
	"fmt"
	"os"

	"sort"
	"strings"
	"time"

	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/ec2"
	"github.com/aws/aws-sdk-go/service/sagemaker"
	"github.com/aws/aws-sdk-go/service/ses"
	"github.com/aws/aws-sdk-go/service/ssm"
)

type UsageLine struct {
	User          string
	Resource      string
	InstanceType  string
	Status        string
	DurationHours float64
	Url           string
}

type AppResources struct {
	SesSource string `json:"ses_source"`
}

type SageMakerResources struct {
	DomainId string `json:"domain_id"`
}

type Member struct {
	Name  string `json:"name"`
	Email string `json:"email"`
}

type TeamConfig struct {
	Admin Member   `json:"admin"`
	Users []Member `json:"users"`
}

var sess *session.Session

func init() {
	sess = session.Must(session.NewSession(&aws.Config{
		Region: aws.String(os.Getenv("AWS_REGION")),
	}))
}

func reportLiveUsage() {
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

	teamConfig := getTeamConfig()
	appResources := getAppResources()
	htmlBody := formatUsageLines(usageLines, teamConfig.Admin.Name, teamConfig.Admin.Name)
	sendEmail(appResources.SesSource, htmlBody, []*string{aws.String(teamConfig.Admin.Email)})

	linesByUser := make(map[string][]UsageLine)
	for _, usageLine := range usageLines {
		linesByUser[usageLine.User] = append(linesByUser[usageLine.User], usageLine)
	}

	emailByName := make(map[string]string)
	for _, user := range teamConfig.Users {
		emailByName[user.Name] = user.Email
	}

	for user, usageLinesForUser := range linesByUser {
		if user == "" {
			continue
		}
		htmlBody := formatUsageLines(usageLinesForUser, teamConfig.Admin.Name, user)
		sendEmail(appResources.SesSource, htmlBody, []*string{&teamConfig.Admin.Email, aws.String(emailByName[user])})
	}
}

func buildEC2UsageLines() []UsageLine {
	ec2Svc := ec2.New(sess)
	var usageLines []UsageLine

	result, err := ec2Svc.DescribeInstances(nil)
	if err != nil {
		fmt.Println("Error describing EC2 instances:", err)
		return usageLines
	}

	for _, res := range result.Reservations {
		for _, instance := range res.Instances {
			if *instance.State.Name != "running" {
				continue
			}
			durationHours := time.Since(*instance.LaunchTime).Hours()
			usageLines = append(usageLines, UsageLine{
				User:          "",
				Resource:      "ec2",
				InstanceType:  *instance.InstanceType,
				Status:        *instance.State.Name,
				DurationHours: durationHours,
				Url:           fmt.Sprintf("https://%s.console.aws.amazon.com/ec2/home#InstanceDetails:instanceId=%s", os.Getenv("AWS_REGION"), *instance.InstanceId),
			})
		}
	}

	return usageLines
}

func buildSageMakerUsageLines() []UsageLine {
	smSvc := sagemaker.New(sess)
	var usageLines []UsageLine

	result, err := smSvc.ListApps(&sagemaker.ListAppsInput{})
	if err != nil {
		panic(fmt.Sprintf("Error listing SageMaker apps: %s", err))
	}

	for _, app := range result.Apps {
		if !(*app.AppType == "KernelGateway" && (*app.Status == "InService" || *app.Status == "Pending")) {
			continue
		}
		durationHours := time.Since(*app.CreationTime).Hours()
		usageLines = append(usageLines, UsageLine{
			Resource:      "sagemaker_kernel",
			InstanceType:  *app.ResourceSpec.InstanceType,
			User:          *app.UserProfileName,
			Status:        *app.Status,
			DurationHours: durationHours,
			Url: fmt.Sprintf("https://%s.console.aws.amazon.com/sagemaker/home?region=%s#/studio/%s/user/%s",
				os.Getenv("AWS_REGION"), os.Getenv("AWS_REGION"), *app.DomainId, *app.UserProfileName),
		})
	}

	return usageLines
}

func formatUsageLines(usageLines []UsageLine, from string, to string) string {
	var htmlRows strings.Builder
	htmlRows.WriteString("<tbody>")
	for _, row := range usageLines {
		htmlRows.WriteString("<tr>")
		htmlRows.WriteString(fmt.Sprintf(`<td>%s</td><td><a href="%s">%s</a></td><td>%s</td><td>%s</td><td>%.2f</td>`,
			row.User, row.Url, row.Resource, row.InstanceType, row.Status, row.DurationHours))
		htmlRows.WriteString("</tr>")
	}
	htmlRows.WriteString("</tbody>")

	header := `
	<thead>
	<th>User</th>
	<th>Resource</th>
	<th>Instance Type</th>
	<th>Status</th>
	<th>Current Session Duration (Hours)</th>
	</thead>
	`
	return fmt.Sprintf(`
	Hello, %s!<br><br>
	The following billable compute resources are currently active:<br><br>
	<table>%s%s</table>
	<br><br>
	Thanks,<br>
	%s
	`, to, header, htmlRows.String(), from)
}

func getTeamConfig() TeamConfig {
	ssmSvc := ssm.New(sess)
	teamConfigParam, err := ssmSvc.GetParameter(&ssm.GetParameterInput{
		Name: aws.String("/collegium/team-config"),
	})
	if err != nil {
		panic(fmt.Sprintf("Error getting TeamConfig: %s", err))
	}
	var teamConfig TeamConfig
	json.Unmarshal([]byte(*teamConfigParam.Parameter.Value), &teamConfig)
	fmt.Printf("TeamConfig = %v\n", teamConfig)
	return teamConfig
}

func getAppResources() AppResources {
	ssmSvc := ssm.New(sess)
	appResourcesParam, err := ssmSvc.GetParameter(&ssm.GetParameterInput{
		Name: aws.String("/collegium/app-resources"),
	})
	if err != nil {
		panic(fmt.Sprintf("Error getting AppResources: %s", err))
	}
	var appResources AppResources
	json.Unmarshal([]byte(*appResourcesParam.Parameter.Value), &appResources)
	fmt.Printf("AppResources = %v\n", appResources)
	return appResources
}

func sendEmail(sesSource string, htmlBody string, recepients []*string) {
	sesSvc := ses.New(sess)
	_, err := sesSvc.SendEmail(&ses.SendEmailInput{
		Source: aws.String(sesSource),
		Destination: &ses.Destination{
			ToAddresses: recepients,
		},
		Message: &ses.Message{
			Subject: &ses.Content{
				Data: aws.String("Collegium - Live Usage"),
			},
			Body: &ses.Body{
				Html: &ses.Content{
					Data: aws.String(htmlBody),
				},
			},
		},
	})
	if err != nil {
		panic(fmt.Sprintf("Error sending email: %s", err))
	}
}

func main() {
	if os.Getenv("AWS_LAMBDA_FUNCTION_NAME") != "" {
		lambda.Start(reportLiveUsage)
	} else {
		reportLiveUsage()
	}
}
