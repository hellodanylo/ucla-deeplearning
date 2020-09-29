terraform {
  backend "s3" {}
}

provider "aws" {
  version = "3.7"
  region  = "us-west-2"
  profile = "ucla"
}

resource "aws_key_pair" "key" {
  key_name   = "ucla-deeplearning"
  public_key = file("${path.module}/key.pub")
}

resource "aws_default_vpc" "default" {}

resource "aws_default_subnet" "default_az1" {
  availability_zone = "us-west-2a"
}

resource "aws_security_group" "ec2_instance" {
  name = "ec2-instance"

  ingress {
    protocol    = "tcp"
    cidr_blocks = [
      "0.0.0.0/0"]
    from_port   = 22
    to_port     = 22
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [
      "0.0.0.0/0"]
  }
}

resource "aws_iam_role" "role" {
  name          = "ucla-deep-learning--ec2"
  assume_role_policy = <<EOF
{
      "Version": "2012-10-17",
      "Statement": [
          {
              "Action": "sts:AssumeRole",
              "Principal": {
                 "Service": "ec2.amazonaws.com"
              },
              "Effect": "Allow",
              "Sid": ""
          }
      ]
  }
  EOF
}

resource "aws_iam_instance_profile" "profile" {
  name = "ucla-deep-learning--ec2"
  role = aws_iam_role.role.name
}

resource aws_instance "instance" {
  tags = {
    Name = "ucla-deeplearning"
  }

  # us-west-2 / Ubuntu 20.04 LTS amd64
  ami           = "ami-06e54d05255faf8f6"
  subnet_id     = aws_default_subnet.default_az1.id
  instance_type = "t3.medium"

  # Security
  key_name = aws_key_pair.key.key_name

  root_block_device {
    volume_size = "100"
    volume_type = "gp2"
  }

  vpc_security_group_ids = [
    aws_security_group.ec2_instance.id]

  iam_instance_profile = aws_iam_instance_profile.profile.name
}

output "ec2" {
  value = {
    instance_name = aws_instance.instance.tags.Name
    instance_id   = aws_instance.instance.id
    public_ip     = aws_instance.instance.public_ip
    username      = "ubuntu"
  }
}
