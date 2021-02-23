import pandas as pd
import re
import sqlite3
import json
from lxml import etree

# Write your code here
print("Input file name: ")
file_name = input()
is_sql = file_name.endswith('.s3db')
is_checked = file_name.endswith('[CHECKED].csv')
is_csv = '.csv' in file_name

if not is_sql:
    if not is_checked:
        if is_csv:
            file = pd.read_csv(file_name)
            file_name = file_name.replace(".csv", "")
        else:
            file = pd.read_excel(file_name, sheet_name="Vehicles")
            file_name = file_name.replace(".xlsx", "")

            csv_name = file_name + ".csv"

            file.to_csv(csv_name, index=None, header=file.columns)

            print(f'{len(file)} {"lines were" if len(file) > 1 else "line was"}'
                  f' imported to {csv_name}')

        output_name = file_name + "[CHECKED].csv"
        correction_count = 0

        for row_index, row in file.iterrows():
            for col_index, item in enumerate(row):
                if not str(item).isdigit():
                    file.iloc[row_index, col_index] = re.search('[0-9]+', item).group()
                    correction_count += 1

        file.to_csv(output_name, index=None, header=file.columns)
        print(f'{correction_count} {"cells were" if correction_count > 1 else "cell was"}'
              f' corrected in {output_name}')

        database_name = output_name.replace("[CHECKED].csv", ".s3db")
    else:
        file = pd.read_csv(file_name)
        database_name = file_name.replace("[CHECKED].csv", ".s3db")

    conn = sqlite3.connect(database_name)
    cursor_name = conn.cursor()
    cursor_name.execute("CREATE TABLE convoy ("
                        "vehicle_id INT PRIMARY KEY,"
                        "engine_capacity INT NOT NULL,"
                        "fuel_consumption INT NOT NULL,"
                        "maximum_load INT NOT NULL"
                        ");")

    for _, row in file.iterrows():
        cursor_name.execute(f"INSERT INTO convoy "
                            f"VALUES ({row[0]}, {row[1]}, {row[2]}, {row[3]});")

    cursor_name.execute("ALTER TABLE convoy "
                        "ADD COLUMN score INT NOT NULL DEFAULT 0;")

    conn.commit()

    print(f"{len(file)} {'records were' if len(file) > 1 else 'record was'}"
          f" inserted into {database_name}")

    json_name = database_name.replace(".s3db", ".json")
    xml_name = database_name.replace(".s3db", ".xml")
else:
    conn = sqlite3.connect(file_name)
    cursor_name = conn.cursor()
    json_name = file_name.replace(".s3db", ".json")
    xml_name = file_name.replace(".s3db", ".xml")

all_records = cursor_name.execute("SELECT *"
                                  "FROM convoy;").fetchall()

convoys = []
xml_str = "<convoy>"
xml_count = 0

for record in all_records:
    vehicle_id = record[0]
    engine_capacity = record[1]
    fuel_consumption = record[2]
    maximum_load = record[3]

    if is_sql:
        score = record[4]
    else:
        score = 0
        if fuel_consumption * 450 / 100 <= 230:
            score += 2
        else:
            score += 1

        pit_stops = fuel_consumption * 450 / 100 / engine_capacity
        if pit_stops < 1:
            score += 2
        elif pit_stops < 2:
            score += 1

        if maximum_load >= 20:
            score += 2

        cursor_name.execute(f"UPDATE convoy "
                            f"SET score = {score} "
                            f"WHERE vehicle_id = {vehicle_id};")

    if score > 3:
        convoys.append({'vehicle_id': vehicle_id,
                        'engine_capacity': engine_capacity,
                        'fuel_consumption': fuel_consumption,
                        'maximum_load': maximum_load})
    else:
        xml_str += f"<vehicle>" \
                   f"<vehicle_id>{vehicle_id}</vehicle_id>" \
                   f"<engine_capacity>{engine_capacity}</engine_capacity>" \
                   f"<fuel_consumption>{fuel_consumption}</fuel_consumption>" \
                   f"<maximum_load>{maximum_load}</maximum_load>" \
                   f"</vehicle>"
        xml_count += 1

if xml_count == 0:
    xml_str += " "
xml_str += "</convoy>"

conn.commit()
conn.close()

with open(json_name, 'w') as json_file:
    json.dump({'convoy': convoys}, json_file)

print(f'{len(convoys)} {"vehicles were" if len(convoys) > 1 else "vehicle was"}'
      f' saved into {json_name}')

root = etree.fromstring(xml_str)
tree = etree.ElementTree(root)
tree.write(xml_name, pretty_print=True, strip_text=True)

print(f'{xml_count} vehicles were'
      f' saved into {xml_name}')
