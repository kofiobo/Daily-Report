import requests
import re
from datetime import datetime

requests.packages.urllib3.disable_warnings()

prtg_servers = [
    {"ip": "10.10.1.116", "username": "prtgadmin", "password": "Kozmik123", "group_name": "Hall Wifi"},
    {"ip": "10.10.1.117", "username": "prtgadmin", "password": "Kozmik123", "group_name": "Faculty LAN"},
    {"ip": "10.10.1.118", "username": "prtgadmin", "password": "Kozmik123", "group_name": "CCTV"},
    {"ip": "10.10.1.120", "username": "prtgadmin", "password": "Kozmik123", "group_name": "Faculty Wifi"},
    {"ip": "10.10.1.122", "username": "prtgadmin", "password": "Kozmik123", "group_name": "Residential LAN"},
    {"ip": "10.10.1.115", "username": "prtgadmin", "password": "Kozmik123", "group_name": "Data center prtg"},
   # {"ip": "10.10.1.123", "username": "prtgadmin", "password": "Kozmik123", "group_name": "Servers"},
    {"ip": "10.10.1.119", "username": "prtgadmin", "password": "Kozmik123", "group_name": "MASTER_CARD"},
    {"ip": "10.10.1.124", "username": "prtgadmin", "password": "Kozmik123", "group_name": "ADMIN_NETWORKS"},
]

def fetch_sensors_with_last_up(prtg_ip, username, password):
    url = f"https://{prtg_ip}/api/table.json"
    params = {
        "content": "sensors",
        "columns": "device,lastup",
        "filter_status": "5",
        "username": username,
        "password": password
    }
    response = requests.get(url, params=params, verify=False)
    sensors = response.json().get("sensors", [])
    return sensors

def write_combined_report(prtg_servers):
    report_filename = "Combined_PRTG_Report.txt"
    with open(report_filename, "w") as file:
        for server in prtg_servers:
            ip = server["ip"]
            username = server["username"]
            password = server["password"]
            group_name = server["group_name"]
            
            print(f"Fetching data from {ip}...")
            sensors = fetch_sensors_with_last_up(ip, username, password)
            
            if sensors:
                file.write(f"--- {group_name} ({ip}) ---\n")
                for sensor in sensors:
                    device_name = sensor.get("device", "Unknown Device")
                    lastup = sensor.get("lastup", "Unknown Last Up Time")
                    file.write(f"{device_name} = {lastup}\n")
            else:
                file.write(f"No sensors with alarms found on {ip} ({group_name}).\n")
            file.write("\n")
    print(f"Combined report saved to {report_filename}")

def generate_critical_sites_report(input_file_path, output_file_path):
    critical_sites = {}
    current_group = None
    
    with open(input_file_path, 'r') as file:
        for line in file:
            if line.startswith("---"):
                current_group = line.strip("- \n")
                critical_sites[current_group] = {}
            elif ' = ' in line and current_group:
                device, status = line.strip().split(' = ')
                
                match = re.search(r'\[(\d+ d)?\s?(\d+ h)?\s?(\d+ m)?\s?(\d+ s)?\s?ago\]', status)
                
                if match:
                    days = int(match.group(1)[:-2]) if match.group(1) else 0
                    hours = int(match.group(2)[:-2]) if match.group(2) else 0
                    minutes = int(match.group(3)[:-2]) if match.group(3) else 0
                    seconds = int(match.group(4)[:-2]) if match.group(4) else 0
                    
                    total_hours = days * 24 + hours + minutes / 60 + seconds / 3600
                    
                    if total_hours <= 15 * 24:
                        downtime = ' '.join(filter(None, [match.group(1), match.group(2), match.group(3), match.group(4)])) + ' ago'
                        critical_sites[current_group][device] = downtime

    with open(output_file_path, 'w') as file:
        now = datetime.now()
        file.write(f"Critical Sites and Downtimes as at {now.strftime('%I:%M%p')} on {now.strftime('%A %d %B %Y')}\n\n")
        
        for group, devices in critical_sites.items():
            if devices:
                file.write(f"*{group}*\n")
                for index, (device, downtime) in enumerate(devices.items(), start=1):
                    file.write(f"{index}. {device} = {downtime}\n")
                file.write("\n")
    
    print(f"Critical sites report generated: {output_file_path}")

def search_device(prtg_servers, search_term):
    results = []
    search_term = search_term.lower() 
    
    for server in prtg_servers:
        ip = server["ip"]
        username = server["username"]
        password = server["password"]
        group_name = server["group_name"]
        
        url = f"https://{ip}/api/table.json"
        params = {
            "content": "devices",
            "columns": "device,status,lastup,downtimesince",
            "username": username,
            "password": password
        }
        try:
            response = requests.get(url, params=params, verify=False)
            response.raise_for_status() 
            devices = response.json().get("devices", [])
            
            for device in devices:
                device_name = device.get("device", "Unknown")
                if search_term in device_name.lower():
                    status = device.get("status", "Unknown")
                    lastup = device.get("lastup", "Unknown")
                    downtimesince = device.get("downtimesince", "")

                    if status == "Up":
                        status_info = "Up"
                    elif status == "Down":
                        status_info = "Down"
                        if downtimesince:
                            downtime_match = re.search(r'\[(\d+ d)?\s?(\d+ h)?\s?(\d+ m)?\s?(\d+ s)?\s?ago\]', downtimesince)
                            if downtime_match:
                                downtime = ' '.join(filter(None, [downtime_match.group(1), downtime_match.group(2), 
                                                                  downtime_match.group(3), downtime_match.group(4)])) + ' ago'
                                status_info += f" for {downtime}"
                    else:
                        status_info = status

                    lastup_match = re.search(r'\[(\d+ d)?\s?(\d+ h)?\s?(\d+ m)?\s?(\d+ s)?\s?ago\]', lastup)
                    if lastup_match:
                        lastup_info = ' '.join(filter(None, [lastup_match.group(1), lastup_match.group(2), 
                                                             lastup_match.group(3), lastup_match.group(4)])) + ' ago'
                    else:
                        lastup_info = lastup

                    results.append({
                        "group": group_name,
                        "prtg_ip": ip,
                        "device_name": device_name,
                        "status": status_info,
                        "lastup": lastup_info
                    })
        except requests.RequestException as e:
            print(f"Error fetching data from {ip}: {str(e)}")
    
    return results

if __name__ == "__main__":
    combined_report_path = "Combined_PRTG_Report.txt"
    critical_sites_report_path = "Critical_Sites_Report.txt"
    
    while True:
        print("\nDAILY REPORT GENERATION:")
        print("1. Critical Sites Reports")
        print("2. Search for a Device")
        print("3. Exit")
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == "1":
            write_combined_report(prtg_servers)
            generate_critical_sites_report(combined_report_path, critical_sites_report_path)
            
            print("\nFirst few lines of the critical sites report:")
            with open(critical_sites_report_path, 'r') as file:
                print(file.read(5000))
        
        elif choice == "2":
            search_term = input("Enter the search term for the device: ")
            results = search_device(prtg_servers, search_term)
            
            if results:
                print(f"\nFound {len(results)} matching device(s):")
                for result in results:
                    print(f"Group: {result['group']}")
                    print(f"PRTG IP: {result['prtg_ip']}")
                    print(f"Device Name: {result['device_name']}")
                    print("---")
            else:
                print(f"No devices found matching '{search_term}'")
        
        elif choice == "3":
            print("Exiting the program. Goodbye!")
            break
        
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")