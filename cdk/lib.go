package lib

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/ses"
	"github.com/aws/aws-sdk-go/service/ssm"
)

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

func InitSession() {
	sess = session.Must(session.NewSession(&aws.Config{
		Region: aws.String(os.Getenv("AWS_REGION")),
	}))
}

func GetSession() *session.Session {
	return sess
}

func GetTeamConfig() TeamConfig {
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

func GetAppResources() AppResources {
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

func SendEmail(title string, htmlBody string, recepients []*string, replyTo string) {
	sesSource := GetAppResources().SesSource
	sesSvc := ses.New(sess)
	_, err := sesSvc.SendEmail(&ses.SendEmailInput{
		Source: aws.String(sesSource),
		Destination: &ses.Destination{
			ToAddresses: recepients,
		},
		ReplyToAddresses: []*string{&replyTo},
		Message: &ses.Message{
			Subject: &ses.Content{
				Data: aws.String(title),
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
