# Jupyter on AWS EC2 Instance

First, create a new AWS account and apply credits from AWS Educate.
Run the following commands in the terminal with `ucla-dev` environment activated.

To enable access to your AWS account:

```
./dev/cli.py aws-up
```

You can find your AWS credentials at AWS Educate -> Vocareum Dashboard -> Account Details -> AWS CLI.

To create the EC2 instance (takes about 10 minutes):

```
./dev/cli.py ec2-up
```

To create a tunnel with the running EC2 instance (do not exit until you are done):

```
./dev/cli.py ec2-tunnel
```

While in the EC2 instance's terminal, you can run `htop` to see CPU cores and CPU RAM utilization.
All other commands (e.g. `jupyter-up`) must run in another terminal, while the tunnel is up.

To create and start the Jupyter container on the EC2 instance (requires the EC2 tunnel to be running):

```
./dev/cli.py jupyter-up --remote
```

You will see a URL and a token in the output. Enter it in the browser.

To change the instance size (for example to t2.2xlarge):

```
./dev/cli.py ec2-resize t2.2xlarge
```

See the AWS slides for information on available instance sizes. Note that resizing also restarts the instance.

To stop the EC2 instance (compute time not billed, data preserved and billed):

```
./dev/cli.py ec2-stop
```

To start the instance after it's been stopped:

```
./dev/cli.py ec2-start
```

To remove the EC2 instance (data removed and not billed), when you have finished this course:

```
./dev/cli.py ec2-down
```

To remove all AWS resources associated with this project, when you have finished this course:

```
./dev/cli.py aws-down
```
