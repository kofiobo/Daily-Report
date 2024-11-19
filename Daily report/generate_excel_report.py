import pandas as pd
import re
from datetime import datetime, timedelta

def parse_combined_report(file_path):
    data = []
    current_group = None

    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith("---"):
                current_group = line.strip("- \n")
            elif ' = ' in line and current_group:
                device, status = line.split(' = ')
                device = device.strip()
                status = status.strip()
                
                # Extract the downtime information
                match = re.search(r'\[(.*?) ago\]', status)
                if match:
                    downtime = match.group(1)
                    # Calculate the date when the device went down
                    time_parts = re.findall(r'(\d+)\s([dhms])', downtime)
                    delta = timedelta()
                    for value, unit in time_parts:
                        if unit == 'd':
                            delta += timedelta(days=int(value))
                        elif unit == 'h':
                            delta += timedelta(hours=int(value))
                        elif unit == 'm':
                            delta += timedelta(minutes=int(value))
                        elif unit == 's':
                            delta += timedelta(seconds=int(value))
                    went_down_date = datetime.now() - delta
                    went_down_date_str = went_down_date.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    downtime = "Unknown"
                    went_down_date_str = "Unknown"

                data.append({
                    "Group": current_group,
                    "Device Name": device,
                    "Downtime": downtime,
                    "Went Down Date": went_down_date_str
                })

    return data

def generate_excel_report(data, output_file_path):
    df = pd.DataFrame(data)
    df.to_excel(output_file_path, index=False)
    print(f"Excel report generated: {output_file_path}")

if __name__ == "__main__":
    combined_report_path = "Combined_PRTG_Report.txt"
    excel_report_path = "PRTG_Report.xlsx"

    report_data = parse_combined_report(combined_report_path)
    generate_excel_report(report_data, excel_report_path)