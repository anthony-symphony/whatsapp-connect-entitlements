# Symphony WeChat & WhatsApp Connect Entitlements

## Overview
This Python script allows you to add / remove users to the Symphony WeChat & WhatsApp Connect entitlements.
Users who are added to the WeChat & WhatsApp Connect entitlements will have access to the Onboarding App which will allow
he/she to onboard users on WeChat & WhatsApp.

The script will be able to perform the following:
- Lookup user(s) Symphony UserID based on given email address
- Add user(s) to WeChat & WhatsApp Connect entitlements
- Install WeChat / WhatsApp Connect Extension App to User profile
- Remove user(s) to WeChat & WhatsApp Connect entitlements
- Remove WeChat / WhatsApp Connect Extension App from User profile
- Get list of users who currently have the entitlement

The script expects a CSV file as input.
Upon completion, the script will produce an CSV file as output containing the results.

The input and output file names can be adjusted at the top of the script. 
The user file name will be used to generate the list of all users who currently have the entitlement 

    # Input/Output File Names
    INPUT_FILE = 'user_entitlements.csv'
    OUTPUT_FILE = 'user_entitlements_output.csv'
    USER_FILE = 'current_user_list.csv'

## Input CSV Columns
The script expects an input CSV file at the top directory where the script runs with filename - ``user_entitlements.csv``

The CSV file will contain following columns:
- UserID (Symphony User ID - e.g ``351775001412105`` - Optional if email address is provided)
- Email (Symphony User Email Address - will be used to lookup UserID from Symphony Pod - Ignored if UserID is not blank)
- Action (Whether to add or remove user to the entitlement - values: ``ADD`` or ``REMOVE``)


## Output CSV Columns
The output file will be saved in the same directory as the input file with filename - ``user_entitlements_output.csv``

Columns will be same as Input CSV above, with additional of **Status** column.

Successful entries will be marked with status = OK. Otherwise, error / more info will be displayed

## User File CSV Columns
The script will also get the latest list of all users who currently have the entitlements.
The output file will be saved in the same directory as the input file with filename - ``current_user_list.csv``

The CSV file will contain following columns:
- UserID (Symphony User ID - e.g ``351775001412105``)
- First Name
- Last Name
- Display Name
- Entitlement Type (``WHATSAPPGROUPS`` or ``WECHAT`` for now)


## Environment Setup
This client is compatible with **Python 3.6 or above**

Create a virtual environment by executing the following command **(optional)**:
``python3 -m venv ./venv``

Activate the virtual environment **(optional)**:
``source ./venv/bin/activate``

Install dependencies required for this client by executing the command below.
``pip install -r requirements.txt``


## Getting Started
### 1 - Prepare RSA Key pair
You will first need to generate a **RSA Public/Private Key Pair**.
- Send the **Public** key to Symphony Support Team in order to set up 
- Private Key will be required in steps below
- In return, Symphony team will provide a publicKeyID which you will need to populate in the config.json file below

For the purpose of User ID lookup and Extension App Installation / Removal. You will also need to set up a [Symphony Service Account](https://support.symphony.com/hc/en-us/articles/360000720863-Create-a-new-service-account), which is a type of account that applications use to work with Symphony APIs. Please contact with Symphony Admin in your company to get the account.

**RSA Public/Private Key Pair** is the recommended authentication mechanism by Symphony, due to its robust security and simplicity.

**Important** - The service account must have **User Provisioning** role in order to work.

### 2 - Upload Service Account Private Key
Please copy the private key file (*.pem) to the **rsa** folder. You will need to configure this in the next step.

Please also upload the private key for Symphony Service Account created above in **rsa** folder.

### 3 - Update resources/config.json

To run the script, you will need to configure **config.json** provided in the **resources** directory. 

**Notes:**

You also need to update based on the service account created above:
- apiURL (please confirm this with Symphony team)
- privateKeyPath (ends with a trailing "/"))
- privateKeyName
- publicKeyId (please confirm this with Symphony team)
- podId (please confirm this with Symphony team)
- entitlementType (please set to either ``WECHAT`` or ``WHATSAPP``)
- appId (please set to either ``wechat`` or ``com.symphony.sfs.admin-app`` for WhatsApp, leave blank if you wish to manage extension app manually)


Sample:

    {
      "apiURL": "xxx.symphony.com",
      "privateKeyPath":"./rsa/",
      "privateKeyName": "privateKey.pem",
      "publicKeyId": "xxx",
      "podId": "xxx",
      "entitlementType": "WECHAT",
      "appId": "wechat",
      "proxyURL": "",
      "proxyUsername": "",
      "proxyPassword": "",
      "truststorePath": ""
    }


### 4 - Update resources/symphony_config.json

In order to perform UserID lookup and Extension App management for Symphony User, you will need to configure this file for access to your Symphony Pod.

Sample:

    {
      "sessionAuthHost": "<POD>.symphony.com",
      "sessionAuthPort": 443,
      "keyAuthHost": "<POD-KM>.symphony.com",
      "keyAuthPort": 443,
      "podHost": "<POD>.symphony.com",
      "podPort": 443,
      "agentHost": "<POD-AGENT>.symphony.com",
      "agentPort": 443,
      "authType": "rsa",
      "botPrivateKeyPath":"./rsa/",
      "botPrivateKeyName": "<Service_Account>-private-key.pem",
      "botCertPath": "",
      "botCertName": "",
      "botCertPassword": "",
      "botUsername": "<Service_Account>",
      "botEmailAddress": "<Service_Account>@symphony.com",
      "appCertPath": "",
      "appCertName": "",
      "appCertPassword": "",
      "authTokenRefreshPeriod": "30",
      "proxyURL": "",
      "proxyUsername": "",
      "proxyPassword": "",
      "podProxyURL": "",
      "podProxyUsername": "",
      "podProxyPassword": "",
      "agentProxyURL": "",
      "agentProxyUsername": "",
      "agentProxyPassword": "",
      "keyManagerProxyURL": "",
      "keyManagerProxyUsername": "",
      "keyManagerProxyPassword": "",
      "truststorePath": ""
    }


### 5 - Run script
The script can be executed by running
``python3 main.py`` 



# Release Notes

## 0.1
- Initial Release

## 0.2
- Add Support for User ID lookup & Extension App management

