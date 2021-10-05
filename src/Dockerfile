FROM amazonlinux:2.0.20210617.0

# prereqs
RUN yum update -y && \
	yum install python3 -y && \
	yum install unzip -y


# install aws cli
RUN /usr/bin/curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" &&\
	/usr/bin/unzip awscliv2.zip &&\
	./aws/install && \
	rm awscliv2.zip

RUN /usr/local/bin/aws configure set default.s3.max_concurrent_requests 20 && \
	/usr/local/bin/aws configure set default.s3.max_queue_size 10000 && \
	/usr/local/bin/aws configure set default.s3.multipart_threshold 64MB && \
	/usr/local/bin/aws configure set default.s3.multipart_chunksize 16MB && \
	# /usr/local/bin/aws configure set default.s3.use_accelerate_endpoint true && \
	/usr/local/bin/aws configure set default.s3.addressing_style path

# boto 3
RUN /usr/bin/pip3 install boto3

# cleanup
RUN yum clean all && \
	rm -rf /var/cache/yum


COPY s3CopySyncScript.py .

# CMD is set in the batch job definition
# CMD ["python3","s3CopySyncScript.py"]
