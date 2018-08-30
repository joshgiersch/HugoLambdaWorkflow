#for local testing, set the following in config.py:
#sourceBucketName, destinationBucketName, sourceSite (to support multiple Hugo sites in one bucket)
#downloadDirectory, executableLocation, outputDirectory
#and cloudfrontDistributionID
maxThreads = 10

#imports
import boto3
import os
import subprocess
import datetime
from concurrent.futures import ThreadPoolExecutor
import mimetypes
import config

# misc variable definition
sourceKeyPrefix = config.sourceSiteName + "/"

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

def threaded_download(sourceBucket, filename, destination):
    sourceBucket.download_file(filename, destination)

def threaded_upload(destinationBucket, sourceFile, keyString, ExtraArgs):
    destinationBucket.upload_file(sourceFile, keyString, ExtraArgs)

def main(event={}):
    #Open bucket
    s3 = boto3.resource("s3")
    sourceBucket = s3.Bucket(config.sourceBucketName)

    #Slurp aaaallllll the files locally
    with ThreadPoolExecutor(max_workers = maxThreads) as executor:
        for obj in sourceBucket.objects.filter(Prefix=sourceKeyPrefix):
            fileString = obj.key
            fileName = fileString.split("/")[-1]
            directoryName = fileString[:-len(fileName)]

            #Create subdirectories based on keys
            if not os.path.exists(config.downloadDirectory + directoryName):
                os.makedirs(config.downloadDirectory + directoryName)
            executor.submit(threaded_download, sourceBucket, fileString, config.downloadDirectory + fileString)

    # Execute Hugo against downloaded files
    flags = "--source " + config.downloadDirectory + config.sourceSiteName + " --destination " + config.outputDirectory
    subprocess.run(config.executableLocation + " " + flags, shell=True)

    # Upload contents of outputDirectory to S3 bucket
    destinationBucket = s3.Bucket(config.destinationBucketName)

    with ThreadPoolExecutor(max_workers = maxThreads) as executor:
        for root, _dirs, files in os.walk(config.outputDirectory):
            for file in files:
                sourceFile = os.path.join(root, file)
                keyString = remove_prefix(sourceFile, config.outputDirectory)
                mimeType = mimetypes.guess_type(keyString)
                executor.submit(threaded_upload, destinationBucket, sourceFile, keyString, ExtraArgs = {"ContentType": mimeType, "ACL": "public-read"})

    # Cloudfront invalidate
    cloudfront = boto3.client("cloudfront")
    invalidationBatch = {'CallerReference':str(int(datetime.datetime.now().timestamp())), 'Paths':{'Quantity': 1, 'Items':['/*']}}
    cloudfront.create_invalidation(DistributionId = config.cloudfrontDistributionID, InvalidationBatch = invalidationBatch)

def AWSLambdaHandler(event, context):
    #force variables to Lambda-friendly locations
    config.downloadDirectory = "/tmp/input/"
    config.outputDirectory = "/tmp/output/"
    config.executableLocation = "./hugo"
    #don't forget to include the hugo executable in the root of your zipfile that you upload to Lambda
    main(event)
    return None

if __name__== "__main__":
    main()