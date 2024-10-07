import aws_cdk.aws_iam as iam
import aws_cdk.aws_sagemaker as sm
import aws_cdk.aws_secretsmanager as s
import aws_cdk.aws_budgets as b
from aws_cdk import Stack, CfnTag
from constructs import Construct

from collegium.cdk.environment import Member, TeamConfig


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
            ),
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:HeadObject"],
                resources=["arn:aws:s3:::danylo-ucla/*", "arn:aws:s3:::sagemaker-*/*"],
            ),
            iam.PolicyStatement(
                actions=["s3:HeadBucket", "s3:ListBucket", "s3:Get*"],
                resources=["arn:aws:s3:::danylo-ucla", "arn:aws:s3:::sagemaker-*"],
            ),
            iam.PolicyStatement(
                actions=["sagemaker:GetSagemakerServicecatalog*"],
                resources=["*"],
            ),
            iam.PolicyStatement(
                actions=["servicecatalog:ListAcceptedPortfolioShares"],
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
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal('sagemaker.amazonaws.com'), # type: ignore
                iam.AccountRootPrincipal(), # type: ignore
            )
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
            self, 'BudgetAnnual-r7',
            budget=b.CfnBudget.BudgetDataProperty(
                budget_type='COST',
                time_unit='ANNUALLY',
                budget_limit=b.CfnBudget.SpendProperty(amount=80, unit='USD'),
                budget_name=f"{member.name}-full-r7",
                cost_filters={
                    "TagKeyValue": [
                        f"user:owner${member.name}"
                    ],
                },
                cost_types=b.CfnBudget.CostTypesProperty(
                    include_credit=False,
                ),
            ),
            notifications_with_subscribers=[
                self.build_subscription(threshold, member, admin_email)
                for threshold in [0, 25, 50, 75, 90, 100]
            ]
        )

        # b.CfnBudget(
        #     self, 'BudgetDaily-r4',
        #     budget=b.CfnBudget.BudgetDataProperty(
        #         budget_type='COST',
        #         time_unit='DAILY',
        #         budget_limit=b.CfnBudget.SpendProperty(amount=20, unit='USD'),
        #         budget_name=f"{member.name}-daily-r4",
        #         cost_filters={
        #             "TagKeyValue": [
        #                 f"user:owner${member.name}"
        #             ],
        #         }
        #     ),
        #     notifications_with_subscribers=[
        #         self.build_subscription(threshold, member, admin_email)
        #         for threshold in [0, 25, 50, 75, 100]
        #     ]
        # )


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
        for policy in ['AmazonSageMakerReadOnly', 'AWSCodeCommitReadOnly', 'IAMUserChangePassword', 'AmazonEC2ContainerRegistryReadOnly', 'AWSBudgetsReadOnlyAccess', 'AmazonRekognitionReadOnlyAccess', 'CloudWatchLogsFullAccess']:
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
                budget_limit=b.CfnBudget.SpendProperty(amount=80*len(self.team_config.users), unit='USD'),
                budget_name=f"team-full",
                cost_types=b.CfnBudget.CostTypesProperty(
                    include_credit=False,
                ),
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
                cost_types=b.CfnBudget.CostTypesProperty(
                    include_credit=False,
                ),
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
            