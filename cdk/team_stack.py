from typing import List
from attr import dataclass
import aws_cdk.aws_iam as iam
import aws_cdk.aws_sagemaker as sm
import aws_cdk.aws_secretsmanager as s
import aws_cdk.aws_budgets as b
from aws_cdk import Stack, Duration, CfnTag
from constructs import Construct
import hashlib


@dataclass
class Member:
    name: str
    email: str


class MemberConstruct(Construct):
    def __init__(self, scope: Construct, id: str, member: Member, domain_id: str):
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
            self, 'Budget',
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
            )
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
        team: List[Member],
        domain_id: str,
    ):
        super().__init__(scope, id)
        self.team_meta = team

        self.team_constructs = [
            MemberConstruct(self, f"Member{member.name.capitalize()}", member, domain_id)
            for member in team
        ]
            