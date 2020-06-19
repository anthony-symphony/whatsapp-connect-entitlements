import csv, sys, traceback
from modules.rsa_auth import SymBotRSAAuth
from modules.configure import SymConfig
from modules.entitlement_client import EntitlementClient

# Input/Output File Names
INPUT_FILE = 'whatsapp_user_entitlements.csv'
OUTPUT_FILE = 'whatsapp_user_entitlements_output.csv'
USER_FILE = 'current_user_list.csv'

def main():
    print('Python Client runs using RSA authentication')

    # RSA Auth flow: pass path to rsa config.json file
    configure = SymConfig('./resources/config.json')
    configure.load_config()
    auth = SymBotRSAAuth(configure)
    entitlement_client = EntitlementClient(auth, configure)

    # Now process CSV file
    # CSV file will have 2 columns - UserID, Action (ADD / REMOVE)
    process_result = []
    with open(INPUT_FILE, newline='') as csvfile:
        csv_list = csv.reader(csvfile, delimiter=',')
        for row in csv_list:
            # Ignore blank rows
            if len(row) == 0:
                continue

            # Ensure CSV has 2 columns
            if len(row) < 2:
                raise Exception(
                    'Invalid CSV File Format - Expect 2 columns - UserID, Action')

            # Skip header row
            if row[0] == "UserID":
                continue

            result_record = dict()
            # Get row values
            result_record['result'] = ''
            result_record['user_id'] = row[0]
            result_record['action'] = row[1].upper()

            # Check if valid Action
            if result_record['action'] != "ADD" and result_record['action'] != "REMOVE":
                result_record['result'] = 'Action is not ADD/REMOVE - SKIPPED'
                process_result.append(result_record)
                continue

            # Add User to Entitlement
            if result_record['action'] == "ADD":
                print(f"Adding {result_record['user_id']}")
                try:
                    output = entitlement_client.add_entitlements(result_record['user_id'])
                    if 'status' in output and 'title' in output:
                        result_record['result'] = f'{output["status"]} - {output["title"]}'
                    if 'displayName' in output:
                        result_record['result'] = f'{output["displayName"]} added successfully'
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

    if 'entitlements' in process_result:
        with open(USER_FILE, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['UserID',
                          'First Name',
                          'Last Name',
                          'Display Name',
                          'Entitlement Type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            for record in process_result['entitlements']:
                writer.writerow(
                    {'UserID': record['symphonyId'],
                     'First Name': record['firstName'] if 'firstName' in record else '',
                     'Last Name': record['lastName'] if 'lastName' in record else '',
                     'Display Name': record['displayName'],
                     'Entitlement Type': record['entitlementType']})

    return


def print_result(process_result):
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['UserID',
                      'Action',
                      'Status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in process_result:
            writer.writerow(
                {'UserID': row['user_id'],
                 'Action': row['action'],
                 'Status': row['result']})

    return

if __name__ == "__main__":
    main()