package main

import (
	"bytes"
	"context"
	_ "embed"
	"fmt"
	"html/template"
	"os"

	"github.com/aws/aws-sdk-go-v2/service/secretsmanager"
	"github.com/aws/aws-sdk-go-v2/service/sts"
	collegium "github.com/hellodanylo/collegium"

	"github.com/aymerick/douceur/inliner"
)

//go:embed welcome_team.html
var welcome_email_html string

type WelcomePackage struct {
	User              collegium.Member
	Admin             collegium.Member
	Password          string
	AccountId         string
	Region            string
	SageMakerDomainId string
}

func formatWelcomeEmail(welcomePackage WelcomePackage) string {
	tmpl, err := template.New("welcome_email").Parse(welcome_email_html)
	if err != nil {
		panic(err)
	}
	var buff bytes.Buffer
	err = tmpl.Execute(&buff, welcomePackage)
	if err != nil {
		panic(err)
	}

	html, err := inliner.Inline(buff.String())
	if err != nil {
		panic(err)
	}
	return html
}

func SendWelcomeEmails(names []string) {
	teamConfig := collegium.GetTeamConfig()
	secm := secretsmanager.NewFromConfig(collegium.GetSession())
	smResources := collegium.GetSageMakerResources()

	sts := sts.NewFromConfig(collegium.GetSession())
	ident, err := sts.GetCallerIdentity(context.TODO(), nil)
	if err != nil {
		panic(err)
	}

	for _, user := range teamConfig.Users {
		if len(names) > 0 {
			match := false
			for _, requested_name := range names {
				if requested_name == user.Name {
					match = true
					break
				}
			}
			if !match {
				continue
			}
		}

		value, err := secm.GetSecretValue(context.TODO(), &secretsmanager.GetSecretValueInput{SecretId: &user.Name})
		if err != nil {
			panic(fmt.Sprintf("Failed to get secret for user %s: %s", user.Name, err))
		}

		pkg := WelcomePackage{User: user, AccountId: *ident.Account, Region: os.Getenv("AWS_REGION"), SageMakerDomainId: smResources.DomainId, Password: *value.SecretString, Admin: teamConfig.Admin}
		html := formatWelcomeEmail(pkg)
		collegium.SendEmail("UCLA MSBA-434 - AWS Cloud Access", html, []string{user.Email, teamConfig.Admin.Email}, teamConfig.Admin.Email)
		fmt.Printf("Sent welcome package to %v\n", user)
	}
}

func main() {
	collegium.InitSession()
	SendWelcomeEmails(os.Args[1:])
}
