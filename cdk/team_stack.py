from typing import List
from dataclasses import dataclass
import aws_cdk.aws_iam as iam
import aws_cdk.aws_sagemaker as sm
import aws_cdk.aws_secretsmanager as s
import aws_cdk.aws_budgets as b
from aws_cdk import Stack, Duration, CfnTag
from constructs import Construct
from dataclass_wizard import JSONWizard


@dataclass
class Member:
    name: str
    email: str


@dataclass
class TeamConfig(JSONWizard):
    admin: Member
    users: List[Member]


class MemberConstruct(Construct):
    def __init__(self, scope: Construct, id: str, member: Member, domain_id: str, admin_email: str):
        super().__init__(scope, id)
        self.member = member
        self.policy = iam.Policy(self, "Policy", policy_name="sagemaker", statements=[
            iam.PolicyStatement(
                actions=["sagemaker:CreatePresignedDomainUrl"],
                resources=[f"arn:aws:sagemaker:*:*:user-profile/*/{member.name}"],
            ),
            iam.PolicyStatement(
                actions=["*"],
                resources=[f"arn:aws:sagemaker:*:*:app/{domain_id}/{member.name}/*/*"],
            ),
            iam.PolicyStatement(
                actions=["license-manager:ListReceivedLicenses"],
                resources=["*"],
            )
        ])

        self.password: s.Secret = s.Secret(
            self, 'Password', 
            generate_secret_string=s.SecretStringGenerator(), 
            secret_name=member.name
        )

        self.user: iam.User = iam.User(
            self, "User", 
            user_name=member.name,
            password=self.password.secret_value
        )
        self.add_permissions(self.user)
        
        self.role: iam.Role = iam.Role(
            self, "Role", 
            assumed_by=iam.ServicePrincipal('sagemaker.amazonaws.com'),
        )
        self.add_permissions(self.role)

        self.domain_user = sm.CfnUserProfile(
            self, 'DomainUser', 
            domain_id=domain_id, 
            user_profile_name=member.name,
            user_settings=sm.CfnUserProfile.UserSettingsProperty(
                execution_role=self.role.role_arn
            ),
            tags=[
                CfnTag(key="owner", value=member.name),
            ]
        )

        b.CfnBudget(
            self, 'BudgetAnnual',
            budget=b.CfnBudget.BudgetDataProperty(
                budget_type='COST',
                time_unit='ANNUALLY',
                budget_limit=b.CfnBudget.SpendProperty(amount=70, unit='USD'),
                budget_name=f"{member.name}-full",
                cost_filters={
                    "TagKeyValue": [
                        f"user:owner${member.name}"
                    ],
                }
            ),
            notifications_with_subscribers=[
                self.build_subscription(threshold, member, admin_email)
                for threshold in [0, 25, 50, 75, 90, 100]
            ]
        )

        b.CfnBudget(
            self, 'BudgetDaily',
            budget=b.CfnBudget.BudgetDataProperty(
                budget_type='COST',
                time_unit='DAILY',
                budget_limit=b.CfnBudget.SpendProperty(amount=10, unit='USD'),
                budget_name=f"{member.name}-daily",
                cost_filters={
                    "TagKeyValue": [
                        f"user:owner${member.name}"
                    ],
                }
            ),
            notifications_with_subscribers=[
                self.build_subscription(threshold, member, admin_email)
                for threshold in [0, 25, 50, 75, 100]
            ]
        )


    def build_subscription(self, threshold: int, member: Member, admin_email: str):
        return b.CfnBudget.NotificationWithSubscribersProperty(
            notification=b.CfnBudget.NotificationProperty(
                comparison_operator='GREATER_THAN', 
                threshold=threshold,
                threshold_type='PERCENTAGE',
                notification_type='ACTUAL'
            ),
            subscribers=[
                b.CfnBudget.SubscriberProperty(address=member.email, subscription_type='EMAIL'),
                b.CfnBudget.SubscriberProperty(address=admin_email, subscription_type='EMAIL'),
            ]
        )

    def add_permissions(self, identity: iam.IIdentity):
        for policy in ['AmazonSageMakerReadOnly', 'AWSCodeCommitReadOnly', 'IAMUserChangePassword', 'AmazonEC2ContainerRegistryReadOnly', 'AWSBudgetsReadOnlyAccess']:
            identity.add_managed_policy(
                policy=iam.ManagedPolicy.from_aws_managed_policy_name(policy)
            )
        identity.attach_inline_policy(self.policy)


class TeamStack(Stack):
    def __init__(self, 
        scope: Construct, id: str,
        domain_id: str,
        team_config: TeamConfig
    ):
        super().__init__(scope, id)
        self.team_config = team_config

        self.team_constructs = [
            MemberConstruct(self, f"Member{member.name.capitalize()}", member, domain_id, self.team_config.admin.email)
            for member in self.team_config.users
        ]

        b.CfnBudget(
            self, 'BudgetAnnual',
            budget=b.CfnBudget.BudgetDataProperty(
                budget_type='COST',
                time_unit='ANNUALLY',
                budget_limit=b.CfnBudget.SpendProperty(amount=70*len(self.team_config.users), unit='USD'),
                budget_name=f"team-full",
            ),
            notifications_with_subscribers=[
                b.CfnBudget.NotificationWithSubscribersProperty(
                    notification=b.CfnBudget.NotificationProperty(
                        comparison_operator='GREATER_THAN', 
                        threshold=threshold,
                        threshold_type='PERCENTAGE',
                        notification_type='ACTUAL'
                    ),
                    subscribers=[
                        b.CfnBudget.SubscriberProperty(address=self.team_config.admin.email, subscription_type='EMAIL'),
                    ]
                )
                for threshold in [0, 25, 50, 75, 90, 100]
            ]
        )

        b.CfnBudget(
            self, 'BudgetDaily',
            budget=b.CfnBudget.BudgetDataProperty(
                budget_type='COST',
                time_unit='DAILY',
                budget_limit=b.CfnBudget.SpendProperty(amount=100, unit='USD'),
                budget_name=f"team-daily",
            ),
            notifications_with_subscribers=[
                b.CfnBudget.NotificationWithSubscribersProperty(
                    notification=b.CfnBudget.NotificationProperty(
                        comparison_operator='GREATER_THAN', 
                        threshold=threshold,
                        threshold_type='PERCENTAGE',
                        notification_type='ACTUAL'
                    ),
                    subscribers=[
                        b.CfnBudget.SubscriberProperty(address=self.team_config.admin.email, subscription_type='EMAIL'),
                    ]
                )
                for threshold in [0, 25, 50, 75, 100]
            ]
        )
            