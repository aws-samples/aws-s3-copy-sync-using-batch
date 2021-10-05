import ast
import boto3
import subprocess
import sys
import csv
from io import StringIO
from urllib.parse import urlparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

LOGGER = logging.getLogger()


def get_bool_input(input_parameter):
	"""Returns a boolean corresponding to a string "True/False" input
	
	Args:
	    input_parameter (str): String input for a boolean
	
	Returns:
	    bool: True/False input
	"""
	if input_parameter.lower().capitalize() in ["True","False"]:
		return ast.literal_eval(input_parameter.lower().capitalize())
	else:
		return None

class S3SyncUtils:

	def __init__(self):
		self.s3_resource = boto3.resource('s3')

	def __copy_if_exists(self,src_bucket, src_key, src_path,dst_path,delete_destination):
		s3_head_object_response = self.s3_resource.meta.client.head_object(
			Bucket=src_bucket,
			Key=src_key)
		if s3_head_object_response['ContentType'].startswith('application/x-directory'): # sync
			LOGGER.info('Source is a directory! Syncing entire paths.')
			self.__s3_sync_helper(src_path,dst_path,delete_destination)
		else:
			LOGGER.info('File Exists! Overwriting file')
			copy_source = {
				'Bucket': src_bucket,
				'Key': src_key
			}
			dst_bucket_key = dst_path.split('//')[1].split('/',1)
			self.s3_resource.meta.client.copy(CopySource=copy_source, 
						Bucket=dst_bucket_key[0], 
						Key=dst_bucket_key[1],
						ExtraArgs={
							'ACL':'bucket-owner-full-control'
						})

	def __s3_sync_helper(self, src_path, dst_path, delete_destination):
		sync_cmd = ['/usr/local/bin/aws',
				's3',
				'sync',
				src_path,
				dst_path,
				'--acl','bucket-owner-full-control']
		if delete_destination:
			sync_cmd.append('--delete')
		out = subprocess.run(sync_cmd, capture_output=True)
		out = out.stdout.decode()
		LOGGER.info(out)


	def s3_copy_sync(self,input_s3_bucket,input_s3_key, skip_header=True, delete_destination=False):
		"""
		:param input_s3_bucket: bucket name of the input file
		:param input_s3_key: name of the file
		:param skip_header:  boolean  : skip first row if true
		:param delete_destination: boolean : delete destination if true
		:return: None
		"""
		csv_str = self.s3_resource.Object(input_s3_bucket,input_s3_key).get()['Body'].read().decode('utf-8')
		rdr = csv.reader(StringIO(csv_str), delimiter=',')
		if skip_header:
			next(rdr) #skip the header row
		#loop over each file/path given as src/destination.
		for row in rdr:
			source=row[0]
			dest=row[1]
			LOGGER.info(f'Source:: {source} Dest:: {dest}')
			# split the S3 path for source into what would be bucket and key
			# EG: s3://bucket-name/some/path/file.txt --> bucket-name, some/path/file.txt
			parsed_s3_url = urlparse(source)
			bucket_src = parsed_s3_url.netloc
			key_src = parsed_s3_url.path[1:] # remove first "/" for a valid s3 key
			self.__copy_if_exists(bucket_src,key_src,source,dest,delete_destination)

def main(argv):
	if len(argv) != 5:
		LOGGER.info("Syntax: python s3CopySyncScript.py <<bucket containing input .csv file>> <<key of input .csv file>> <<header True/False>> <<sync_delete True/False>>")
		sys.exit(1)

	LOGGER.info(f"Received {len(argv)} arguments:\n"
		f"\tInput csv file bucket name ::: {argv[1]}\n"
		f"\tInput csv file file name ::: {argv[2]}\n"
		f"\tFile containing header ::: {argv[3]}\n"
		f"\tDelete destination files ::: {argv[4]}" )

	S3_UTILS = S3SyncUtils()
	header_input = get_bool_input(argv[3])
	delete_input = get_bool_input(argv[4])
	if header_input is None or delete_input is None:
		LOGGER.error("Incorrect input, the HEADER must be true/false and delete files must be true or false")
		sys.exit(2)
	S3_UTILS.s3_copy_sync(argv[1],argv[2],header_input,delete_input)


if __name__ == '__main__':
	main(sys.argv)
