## Email Attachment Extractor

The email attachment extractor allows you to download email attachments from the POP3 mailbox. There is no restriction for attachment type, so you can download also XLS files or images. 

## Configuration

A configuration consist of mostly mandatory parameters. A sample configuration can be found in the [component's repository](https://github.com/Phalanx-Ai/ex-pop3-attachment) 

* POP3 server (`server`) - a name or IP address of the POP3 server
* username (`username`) - a username used to login to POP3 server
* password (`#password`) - a password associated with username
* valid email address (`accept_from`) - accept only emails from a given address
* valid filename of attachment (`accept_filename`) - accept only attachments with a given filename

## Output

A file with content of email attachment, the name matches the filename of the attachment. 
