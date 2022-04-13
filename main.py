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
    if configure.data["appId"] != '':
        pod_user_client = PodUserClient(configure.data["appId"])
    else:
        pod_user_client = None

    # Now process CSV file
    # CSV file will have 2 columns - advisorSymphonyId, Action, Permission (ADD / REMOVE)
    process_result = []
    with open(INPUT_FILE, newline='') as csvfile:
        csv_list = csv.reader(csvfile, delimiter=',')
        for row in csv_list:
            # Ignore blank rows
            if len(row) == 0:
                continue

            # Ensure CSV has 3 columns
            if len(row) !=3 :
                raise Exception(
                    'Invalid CSV File Format - Expect 3 columns - advisorSymphonyId, Action, Permissions')

            # Skip header row
            if row[0] == "advisorSymphonyId":
                continue

            result_record = dict()
            # Get row values
            result_record['result'] = ''
            result_record['advisorSymphonyId'] = row[0].lower()
            result_record['ent_action'] = row[1].upper()
            result_record['permission'] = row[2]

            # Check if valid Entitlement Action
            if result_record['ent_action'] not in ("ADD", "REMOVE", ""):
                result_record['result'] = 'ERROR - Invalid Entitlement Action - SKIPPED'
                process_result.append(result_record)
                continue

            # If advisorSymphonyId is blank, then SKIP
            if result_record['advisorSymphonyId'] is None or result_record['advisorSymphonyId'] == '':
                result_record['result'] = f'ERROR - advisorSymphonyId field is not populated - SKIPPED'
                process_result.append(result_record)
                continue


            # Add User to Entitlement
            if result_record['ent_action'] == "ADD":
                print(f"Adding {result_record['advisorSymphonyId']}")
                try:
                    output = entitlement_client.add_entitlements(result_record['advisorSymphonyId'])
                    if 'status' in output and 'title' in output:
                        result_record['result'] = f'{output["status"]} - {output["title"]} '
                    else:
                        result_record['result'] = 'User added to Entitlement. '

                        if 'advisorSymphonyId' in output:
                            user_id = output['advisorSymphonyId']
                        if 'symphonyId' in output:
                            user_id = output['symphonyId']

                        # Install Connect App if AppId is set
                        if configure.data["appId"] != '' and user_id != '':
                            print(f"Installing {configure.data['appId']} extension app")
                            if pod_user_client.install_connect_app_by_userid(user_id):
                                result_record['result'] = f'User added to Entitlement. {configure.data["appId"]} extension app installed Successfully!'

                except Exception as ex:
                    exInfo = sys.exc_info()
                    print(f" ##### ERROR WHILE ADDING ENTITLEMENT {result_record['advisorSymphonyId']} #####")
                    print('Stack Trace: ' + ''.join(traceback.format_exception(exInfo[0], exInfo[1], exInfo[2])))
                    result_record['result'] = 'ERROR ADDING Entitlement - Check logs for details'


                # Add Permissions
                if result_record['permission'] is not None and result_record['permission'] != '':
                    print(f"Parsing Permissions")
                    permission_list = result_record['permission'].split("~")

                    if permission_list is not None and len(permission_list) > 0:
                        for p in permission_list:
                            print(f"Adding Permission - {p}")
                            try:
                                output = entitlement_client.add_permission(result_record['advisorSymphonyId'], p)
                                if 'permission' in output:
                                    result_record['result'] += f'Permission {p} added successfully '
                                elif 'status' in output and 'title' in output:
                                    result_record['result'] += f'{output["status"]} - {output["title"]} '
                                else:
                                    result_record['result'] += f'ERROR - Fail to add permission {p} '

                            except Exception as ex:
                                exInfo = sys.exc_info()
                                print(f" ##### ERROR WHILE ADDING PERMISSION {p} for {result_record['advisorSymphonyId']} #####")
                                print(
                                    'Stack Trace: ' + ''.join(traceback.format_exception(exInfo[0], exInfo[1], exInfo[2])))
                                result_record['result'] += f'ERROR ADDING PERMISSION {p} - Check logs for details '

            # Remove User to Entitlement
            if result_record['ent_action'] == "REMOVE":
                print(f"Removing Entitlement - {result_record['advisorSymphonyId']}")
                try:
                    # Get User ID
                    if configure.data["appId"] != '':
                        output = entitlement_client.find_entitlement(result_record['advisorSymphonyId'])
                        if 'advisorSymphonyId' in output:
                            user_id = output['advisorSymphonyId']
                        if 'symphonyId' in output:
                            user_id = output['symphonyId']

                    # Remove Entitlement
                    output = entitlement_client.delete_entitlements(result_record['advisorSymphonyId'])
                    if 'status' in output and 'title' in output:
                        result_record['result'] = f'{output["status"]} - {output["title"]}'
                    else:
                        result_record['result'] = 'Entitlement Removed successfully'

                        # Remove Connect App if AppId is set
                        if configure.data["appId"] != '' and user_id is not None:
                            print(f"Removing {configure.data['appId']} extension app")
                            if pod_user_client.remove_connect_app_by_userid(user_id):
                                result_record['result'] = f'User removed from Entitlement. {configure.data["appId"]} extension app removed Successfully!'

                except Exception as ex:
                    exInfo = sys.exc_info()
                    print(f" ##### ERROR WHILE REMOVING {result_record['advisorSymphonyId']} #####")
                    print('Stack Trace: ' + ''.join(traceback.format_exception(exInfo[0], exInfo[1], exInfo[2])))
                    result_record['result'] = 'ERROR REMOVING Entitlement - Check logs for details'

            # Append Result
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
        fieldnames = ['advisorSymphonyId',
                      'Action',
                      'Permissions',
                      'Status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in process_result:
            writer.writerow(
                {'advisorSymphonyId': row['advisorSymphonyId'],
                 'Action': row['ent_action'],
                 'Permissions': row['permission'],
                 'Status': row['result']})

    return

if __name__ == "__main__":
    main()
