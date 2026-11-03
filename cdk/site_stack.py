import aws_cdk.aws_cloudfront as cf
import aws_cdk.aws_cloudfront_origins as origins
import aws_cdk.aws_iam as iam
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_ssm as ssm
from aws_cdk import Annotations, CfnOutput, Stack
from constructs import Construct

from collegium.cdk.environment import SSMParameter, SiteResources

BUCKET = 'danylo-ucla'
# Rendered lecture notebooks, uploaded by `foundation/cli.py jupyter-process --render`
SITE_PREFIX = 'app/collegium'


class SiteStack(Stack):
    """Public website for the rendered lecture notebooks, served by CloudFront from the private course bucket.

    The bucket blocks all public access; CloudFront reads only SITE_PREFIX through Origin Access Control, so
    datasets and grading files in the same bucket stay unreachable.
    """

    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        bucket = s3.Bucket.from_bucket_name(self, 'Bucket', BUCKET)

        self.distribution = cf.Distribution(
            self, 'Distribution',
            comment='collegium rendered notebooks',
            default_behavior=cf.BehaviorOptions(
                # URLs are https://<domain>/<module>/<notebook>.html
                origin=origins.S3BucketOrigin.with_origin_access_control(bucket, origin_path=f'/{SITE_PREFIX}'),
                viewer_protocol_policy=cf.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cf.CachePolicy.CACHING_OPTIMIZED,
            ),
            price_class=cf.PriceClass.PRICE_CLASS_100,
        )

        # The bucket isn't managed by CDK, so the origin can't attach its statement automatically.
        Annotations.of(self.distribution).acknowledge_warning('@aws-cdk/aws-cloudfront-origins:updateImportedBucketPolicyOac')
        # This becomes the bucket's (only) policy: add any future bucket policy statements here.
        policy = s3.CfnBucketPolicy(
            self, 'BucketPolicy',
            bucket=BUCKET,
            policy_document=iam.PolicyDocument(statements=[
                iam.PolicyStatement(
                    sid='CloudFrontReadsRenderedNotebooks',
                    principals=[iam.ServicePrincipal('cloudfront.amazonaws.com')],
                    actions=['s3:GetObject'],
                    resources=[f'arn:aws:s3:::{BUCKET}/{SITE_PREFIX}/*'],
                    conditions={'StringEquals': {'AWS:SourceArn': self.distribution.distribution_arn}},
                ),
            ]),
        )

        ssm.CfnParameter(
            self, 'SiteResources',
            name=SSMParameter.SITE_RESOURCES.value,
            type='String',
            value=SiteResources(
                bucket=BUCKET,
                prefix=SITE_PREFIX,
                distribution_id=self.distribution.distribution_id,
                domain_name=self.distribution.distribution_domain_name,
            ).to_json(),
        )
        CfnOutput(self, 'SiteUrl', value=f'https://{self.distribution.distribution_domain_name}/')
