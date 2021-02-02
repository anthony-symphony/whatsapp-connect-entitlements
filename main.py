import csv, sys, traceback
from modules.rsa_auth import SymBotRSAAuth
from modules.configure import SymConfig
from modules.entitlement_client import EntitlementClient
from modules.pod_user_client import PodUserClient

# Input/Output File Names
INPUT_FILE = 'whatsapp_user_entitlements.csv'
OUTPUT_FILE = 'whatsapp_user_entitlements_output.csv'
USER_FILE = 'current_user_list.csv'


def main():
    print('Start Processing...')

    # RSA Auth flow: pass path to rsa config.json file
    configure = SymConfig('./resources/config.json')
    configure.load_config()
    entitlement_type = configure.data["entitlementType"]
    auth = SymBotRSAAuth(configure)
    entitlement_client = EntitlementClient(auth, configure, entitlement_type)
    pod_user_client = PodUserClient(configure.data["appId"])

    # Now process CSV file
    # CSV file will have 2 columns - UserID, Action (ADD / REMOVE)
    process_result = []
    with open(INPUT_FILE, newline='') as csvfile:
        csv_list = csv.reader(csvfile, delimiter=',')
        for row in csv_list:
            # Ignore blank rows
            if len(row) == 0:
                continue

            # Ensure CSV has 3 columns
            if len(row) < 3:
                raise Exception(
                    'Invalid CSV File Format - Expect 2 columns - UserID, Email, Action')

            # Skip header row
            if row[0] == "UserID":
                continue

            result_record = dict()
            # Get row values
            result_record['result'] = ''
            result_record['user_id'] = row[0]
            result_record['email'] = row[1].lower()
            result_record['action'] = row[2].upper()

            # Check if valid Action
            if result_record['action'] != "ADD" and result_record['action'] != "REMOVE":
                result_record['result'] = 'Action is not ADD/REMOVE - SKIPPED'
                process_result.append(result_record)
                continue

            # If User ID blank, then search by Email
            if result_record['user_id'] == '' and result_record['email'] != '':
                result_record['user_id'] = pod_user_client.lookup_user_by_email(result_record['email'])

                if result_record['user_id'] is None:
                    result_record['result'] = f'ERROR - User ID not found for given email'
                    process_result.append(result_record)
                    continue


            # Add User to Entitlement
            if result_record['action'] == "ADD":
                print(f"Adding {result_record['user_id']}")
                try:
                    output = entitlement_client.add_entitlements(result_record['user_id'])
                    if 'status' in output and 'title' in output:
                        result_record['result'] = f'{output["status"]} - {output["title"]}'

                    if 'errorMessage' in output:
                        result_record['result'] = output['errorMessage']
                    else:
                        # if successful, get the user email
                        if 'emailAddress' in output and output['emailAddress'] is not None:
                            result_record['email'] = output['emailAddress']
                        else:
                            result_record['result'] = 'Missing Email Address - Unable to add room permission'

                        # Add Room Permission
                        if result_record['email'] is not None and result_record['email'] != '':
                            print(f"Adding create room permission")
                            output = entitlement_client.add_room_permission(result_record['email'])
                            if 'permission' in output:
                                result_record['result'] = f'User added successfully'

                                # Install Connect App if AppId is set
                                if configure.data["appId"] != '':
                                    print(f"Installing {configure.data['appId']} extension app")
                                    if pod_user_client.install_connect_app_by_userid(result_record['user_id']):
                                        result_record['result'] = f'User added to Entitlement. {configure.data["appId"]} extension app installed Successfully!'

                            elif 'status' in output and 'title' in output:
                                result_record['result'] = f'{output["status"]} - {output["title"]}'
                            else:
                                result_record['result'] = f'ERROR - Fail to add room permission'

                except Exception as ex:
                    exInfo = sys.exc_info()
                    print(f" ##### ERROR WHILE ADDING {result_record['user_id']} #####")
                    print('Stack Trace: ' + ''.join(traceback.format_exception(exInfo[0], exInfo[1], exInfo[2])))
                    result_record['result'] = 'ERROR ADDING - Check logs for details'
                    process_result.append(result_record)
                    continue

            # Remove User to Entitlement
            if result_record['action'] == "REMOVE":
                print(f"Removing {result_record['user_id']}")
                try:
                    output = entitlement_client.delete_entitlements(result_record['user_id'])
                    if 'status' in output and 'title' in output:
                        result_record['result'] = f'{output["status"]} - {output["title"]}'
                    else:
                        result_record['result'] = 'Removed successfully'

                        # Remove Connect App if AppId is set
                        if configure.data["appId"] != '':
                            print(f"Removing {configure.data['appId']} extension app")
                            if pod_user_client.remove_connect_app_by_userid(result_record['user_id']):
                                result_record['result'] = f'User removed from Entitlement. {configure.data["appId"]} extension app removed Successfully!'

                except Exception as ex:
                    exInfo = sys.exc_info()
                    print(f" ##### ERROR WHILE REMOVING {result_record['user_id']} #####")
                    print('Stack Trace: ' + ''.join(traceback.format_exception(exInfo[0], exInfo[1], exInfo[2])))
                    result_record['result'] = 'ERROR REMOVING - Check logs for details'
                    process_result.append(result_record)
                    continue

            # Everything done successfully
            process_result.append(result_record)

    # Print final result
    print(f'Generating Result Files...')
    print_result(process_result)

    # Print Current User List
    print(f'Generating Current User List...')
    user_list = entitlement_client.list_entitlements()
    print_curent_user_list(user_list)


def print_curent_user_list(process_result):

    if len(process_result) > 0:
        with open(USER_FILE, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['UserID',
                          'First Name',
                          'Last Name',
                          'Display Name',
                          'External Network']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            for record in process_result:
                writer.writerow(
                    {'UserID': record['symphonyId'],
                     'First Name': record['firstName'] if 'firstName' in record else '',
                     'Last Name': record['lastName'] if 'lastName' in record else '',
                     'Display Name': record['displayName'],
                     'External Network': record['externalNetwork']})

    return


def print_result(process_result):
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['UserID',
                      'Email',
                      'Action',
                      'Status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in process_result:
            writer.writerow(
                {'UserID': row['user_id'],
                 'Email': row['email'],
                 'Action': row['action'],
                 'Status': row['result']})

    return

if __name__ == "__main__":
    main()
