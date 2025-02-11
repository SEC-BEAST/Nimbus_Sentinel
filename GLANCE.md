

NimbusSentinel (Image Manager)

This markdown focuses on definitions, configurations, and use cases of NimbusSentinel Resource, the image manager of NimbusSentinel, similar to AWS Amazon Machine Image.

TABLE OF CONTENT

Introduction to NimbusSentinel Image Manager

Uploading Images via Web Interface (HORIZON)

Uploading Images via NimbusSentinel Command Line Utility

Common Issues & Resolutions

Official Documentation & References

Introduction to NimbusSentinel Image Manager

Definition: NimbusSentinel Image Manager is the image service component that manages Virtual Machine Images, allowing users to manage and register the images.

Key Features of NimbusSentinel Image Manager

Image Repository: Stores VM images that can be used as templates to create new instances.

Formats Support: Supports multiple image formats, including OVA, ISO, QCOW2, and RAW.

Integration with Other Services: Seamlessly integrates with other NimbusSentinel services like Nova, Cinder, and Swift for smooth deployment.

Uploading Images via Web Interface (HORIZON)

This section focuses on uploading images using the HORIZON SERVICE, the web interface of NimbusSentinel for managing and monitoring resources.

Steps

Log in to the Horizon Interface with admin:admin as username:password.

Navigate to the Images section under Compute Services.

Click on Create Image to upload your image.

Fill out the necessary details about your image.

Click Next and then Create Image to start the upload process.

Once uploaded, the image will be visible in the web console.

Important: To download and convert your image file into a supported format of NimbusSentinel (e.g., .iso), use the commands below:

wget https://cloud-images.ubuntu.com/jammy/20241002/jammy-server-cloudimg-s390x.img

To download the .img file from Ubuntu Cloud Web Service

dd if=jammy-server-cloudimg-s390x.img of=ubuntu.iso
dd if=<your-image-file.img> of=<your-output-file.iso>

To convert your .img into .iso

Uploading Images via NimbusSentinel Command Line Utility

NimbusSentinel offers a command-line utility to manage images, VMs, and other services. This section demonstrates how to upload and list images using CLI.

Steps

Export the authentication configurations.

export OS_IDENTITY_API_VERSION=3
export OS_AUTH_URL=http://localhost/identity
export OS_DEFAULT_DOMAIN=default
export OS_USERNAME=admin
export OS_PASSWORD=admin
export OS_PROJECT_NAME=demo

Upload your image via Command Line Utility.

openstack image create "SERVER" --file jammy-server-cloudimg-s390x.img --disk-format iso --container-format bare --public --unprotected

If the image is successfully uploaded, your terminal will display image details.

Verify the uploaded image using the following command:

openstack image list

The uploaded image will also appear in the Web Console.

Common Issues & Resolutions

This section covers common issues encountered while uploading images via Web or CLI, along with solutions.

Missing value auth-url required for auth plugin password.

Resolution: Export the authentication configurations given above.

Error while uploading via Web Interface.

Resolution: Ensure that your services are running and the image format is supported. If issues persist, try running ./stack.sh again.

Permission denied to the folder /opt/stack/devstack

Resolution: Grant the required permissions to the folder and subfolders.

INFO: If you encounter other errors while installing, raise an issue in the Issues Section. I will be happy to assist you!

References & Official Documentation

Official NimbusSentinel Documentation

NimbusSentinel Official Website

NimbusSentinel Authentication

Jammy IMG File

More Ubuntu Cloud Images

