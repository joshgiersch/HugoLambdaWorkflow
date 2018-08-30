# HugoLambdaWorkflow

A Python workflow for updating a statically-hosted S3 site, triggered by updates to an S3 storage bucket. 

This script triggers [Hugo](http://gohugo.io), a static site generator, but you can use it as a template for any sort of "run an arbitrary executable from Python, based on an Amazon Lambda trigger" requirement.

To use: 

* Connect your S3 bucket to trigger an Amazon Lambda event on a new file upload or a file change (github webhooks are a common one)
* Upload this script and the Hugo executable to Lambda in a single zipfile
* Point the script to the "source" and "destination" S3 buckets 
(In production, the "source" bucket and filename will be provided by the AWS S3-Lambda trigger)
* Ensure that when you update or upload a new file to the source bucket, the script triggers and pushes to the "destination" bucket
