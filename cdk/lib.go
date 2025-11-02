package lib

import (
	"context"
	"encoding/json"
	"fmt"
	"os"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/ses"
	ses_types "github.com/aws/aws-sdk-go-v2/service/ses/types"
	"github.com/aws/aws-sdk-go-v2/service/ssm"
)

type AppResources struct {
	SesSource string `json:"ses_source"`
}

type SageMakerResources struct {
	DomainId string `json:"domainId"`
}

type Member struct {
	Name  string `json:"name"`
	Email string `json:"email"`
}

type TeamConfig struct {
	Admin Member   `json:"admin"`
	Users []Member `json:"users"`
}

var sess aws.Config

func InitSession() {
	cfg, _ := config.LoadDefaultConfig(context.TODO(),
		config.WithRegion(os.Getenv("AWS_REGION")),
	)
	sess = cfg
}

func GetSession() aws.Config {
	return sess
}

func GetTeamConfig() TeamConfig {
	ssmSvc := ssm.NewFromConfig(sess)
	teamConfigParam, err := ssmSvc.GetParameter(context.TODO(), &ssm.GetParameterInput{
		Name: aws.String("/collegium/team-config"),
	})
	if err != nil {
		panic(err)
	}

	var teamConfig TeamConfig
	err = json.Unmarshal([]byte(*teamConfigParam.Parameter.Value), &teamConfig)
	if err != nil {
		panic(err)
	}

	fmt.Printf("TeamConfig = %v\n", teamConfig)
	return teamConfig
}

func GetAppResources() AppResources {
	ssmSvc := ssm.NewFromConfig(sess)
	appResourcesParam, err := ssmSvc.GetParameter(context.TODO(), &ssm.GetParameterInput{
		Name: aws.String("/collegium/app-resources"),
	})
	if err != nil {
		panic(fmt.Sprintf("Error getting AppResources: %s", err))
	}
	var appResources AppResources
	err = json.Unmarshal([]byte(*appResourcesParam.Parameter.Value), &appResources)
	if err != nil {
		panic(err)
	}
	return appResources
}

func GetSageMakerResources() SageMakerResources {
	ssmSvc := ssm.NewFromConfig(sess)
	response, err := ssmSvc.GetParameter(context.TODO(), &ssm.GetParameterInput{
		Name: aws.String("/collegium/sagemaker-resources"),
	})
	if err != nil {
		panic(fmt.Sprintf("Error getting SageMakerResources: %s", err))
	}
	var resources SageMakerResources
	err = json.Unmarshal([]byte(*response.Parameter.Value), &resources)
	if err != nil {
		panic(err)
	}
	return resources
}

func SendEmail(title string, htmlBody string, recepients []string, replyTo string) {
	sesSource := GetAppResources().SesSource
	sesSvc := ses.NewFromConfig(sess)
	_, err := sesSvc.SendEmail(context.TODO(), &ses.SendEmailInput{
		Source: aws.String(sesSource),
		Destination: &ses_types.Destination{
			ToAddresses: recepients,
		},
		ReplyToAddresses: []string{replyTo},
		Message: &ses_types.Message{
			Subject: &ses_types.Content{
				Data: aws.String(title),
			},
			Body: &ses_types.Body{
				Html: &ses_types.Content{
					Data: aws.String(htmlBody),
				},
			},
		},
	})
	if err != nil {
		panic(fmt.Sprintf("Error sending email to %v: %s", recepients, err))
	}
}
