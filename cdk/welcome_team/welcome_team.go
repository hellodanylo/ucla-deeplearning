package main

import (
	"bytes"
	_ "embed"
	"html/template"

	"github.com/aws/aws-sdk-go/service/secretsmanager"
	"github.com/aws/aws-sdk-go/service/sts"
	collegium "github.com/hellodanylo/collegium"

	"github.com/aymerick/douceur/inliner"
)

//go:embed welcome_team.html
var welcome_email_html string

type WelcomePackage struct {
	User      collegium.Member
	Admin     collegium.Member
	Password  string
	AccountId string
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

	html, _ := inliner.Inline(buff.String())
	return html
}

func SendWelcomeEmails() {
	teamConfig := collegium.GetTeamConfig()
	secm := secretsmanager.New(collegium.GetSession())
	sts := sts.New(collegium.GetSession())
	ident, _ := sts.GetCallerIdentity(nil)
	for _, user := range teamConfig.Users {
		value, _ := secm.GetSecretValue(&secretsmanager.GetSecretValueInput{SecretId: &user.Name})
		pkg := WelcomePackage{User: user, AccountId: *ident.Account, Password: *value.SecretString, Admin: teamConfig.Admin}
		html := formatWelcomeEmail(pkg)
		collegium.SendEmail("UCLA MSBA-434 - AWS Cloud Access", html, []*string{&user.Email, &teamConfig.Admin.Email}, teamConfig.Admin.Email)
	}
}

func main() {
	collegium.InitSession()
	SendWelcomeEmails()
}
