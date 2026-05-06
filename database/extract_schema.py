import re
import os

input_file = r"d:\Development\Personal\research\database\crafteddb20260505.sql"
output_file = r"d:\Development\Personal\research\database\schema.sql"

def convert_mssql_to_mysql():
    if not os.path.exists(input_file): return

    print(f"Reading {input_file}...")
    try:
        with open(input_file, 'r', encoding='utf-16') as f:
            content = f.read()
    except:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

    print("Indexing Primary Keys...")
    pk_map = {}
    pk_p1 = r"ALTER TABLE \[dbo\]\.\[(.*?)\]\s+ADD\s+CONSTRAINT\s+\[.*?\]\s+PRIMARY\s+KEY\s+CLUSTERED\s*\(\s*(.*?)\s*\)"
    for m in re.finditer(pk_p1, content, re.DOTALL | re.IGNORECASE):
        tbl, cols_raw = m.groups()
        pk_cols = re.findall(r"\[(.*?)\]", cols_raw)
        pk_map[tbl] = ", ".join([f"`{c}`" for c in pk_cols])

    pk_p2 = r"CREATE TABLE \[dbo\]\.\[(.*?)\].*?CONSTRAINT\s+\[.*?\]\s+PRIMARY\s+KEY\s+CLUSTERED\s*\((.*?)\)"
    for m in re.finditer(pk_p2, content, re.DOTALL | re.IGNORECASE):
        tbl, cols_raw = m.groups()
        if tbl not in pk_map:
            pk_cols = re.findall(r"\[(.*?)\]", cols_raw)
            pk_map[tbl] = ", ".join([f"`{c}`" for c in pk_cols])

    print("Indexing Foreign Keys...")
    fk_list = []
    fk_pattern = r"ALTER TABLE \[dbo\]\.\[(.*?)\]\s+WITH CHECK ADD\s+CONSTRAINT\s+\[(.*?)\]\s+FOREIGN KEY\(\[(.*?)\]\)\s+REFERENCES \[dbo\]\.\[(.*?)\] \(\[(.*?)\]\)"
    for m in re.finditer(fk_pattern, content, re.IGNORECASE):
        source_tbl, constraint_name, source_col, target_tbl, target_col = m.groups()
        fk_list.append(f"ALTER TABLE `{source_tbl}` ADD CONSTRAINT `{constraint_name}` FOREIGN KEY (`{source_col}`) REFERENCES `{target_tbl}` (`{target_col}`);")

    schema_out = "SET FOREIGN_KEY_CHECKS = 0;\n\n"

    blocks = content.split("CREATE TABLE [dbo].[")
    print(f"Processing {len(blocks)-1} tables...")

    for block in blocks[1:]:
        table_name = block.split("]")[0]
        try:
            start_idx = block.find("(")
            if start_idx == -1: continue
            
            depth = 0
            end_idx = -1
            for i in range(start_idx, len(block)):
                if block[i] == '(': depth += 1
                elif block[i] == ')':
                    depth -= 1
                    if depth == 0:
                        end_idx = i
                        break
            
            if end_idx == -1: continue
            inner_content = block[start_idx+1:end_idx]
            clean_cols_block = re.split(r"\s+CONSTRAINT\s+", inner_content, flags=re.IGNORECASE)[0]
            
            mysql_cols = []
            for line in clean_cols_block.split('\n'):
                line = line.strip()
                if not line or line.startswith("CONSTRAINT") or line.startswith("PRIMARY KEY") or line == "(" or line == ")":
                    continue
                
                # 1. DataType mapping BEFORE backticks
                line = re.sub(r"\[int\]|int", "INT", line, flags=re.IGNORECASE)
                line = re.sub(r"IDENTITY\(\d+,\s*\d+\)", "AUTO_INCREMENT", line, flags=re.IGNORECASE)
                line = re.sub(r"\[nvarchar\]\(max\)|nvarchar\(max\)", "TEXT", line, flags=re.IGNORECASE)
                line = re.sub(r"\[nvarchar\]|nvarchar", "VARCHAR", line, flags=re.IGNORECASE)
                line = re.sub(r"\[bit\]|bit", "TINYINT(1)", line, flags=re.IGNORECASE)
                line = re.sub(r"\[uniqueidentifier\]|uniqueidentifier", "VARCHAR(36)", line, flags=re.IGNORECASE)
                line = re.sub(r"\[datetime2\]\(\d+\)|datetime2|\[datetime\]|datetime", "DATETIME", line, flags=re.IGNORECASE)
                line = re.sub(r"\[xml\]|xml", "TEXT", line, flags=re.IGNORECASE)
                line = re.sub(r"\[decimal\]|decimal", "DECIMAL", line, flags=re.IGNORECASE)
                line = re.sub(r"\[varbinary\]\(max\)|varbinary\(max\)", "LONGBLOB", line, flags=re.IGNORECASE)
                line = re.sub(r"NOT FOR REPLICATION", "", line, flags=re.IGNORECASE)
                
                # 2. Cleanup brackets and schema (now only for column names)
                line = re.sub(r"\[dbo\]\.", "", line)
                line = re.sub(r"\[(.*?)\]", r"`\1`", line)
                
                line = line.rstrip(',')
                if line and "`" in line and not line.strip().startswith("`Id` ASC"):
                    mysql_cols.append(f"  {line}")
            
            mysql_table = f"CREATE TABLE `{table_name}`(\n"
            mysql_table += ",\n".join(mysql_cols)
            if table_name in pk_map:
                mysql_table += f",\n  PRIMARY KEY ({pk_map[table_name]})"
            
            mysql_table += "\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\n\n"
            schema_out += mysql_table
        except: continue

    schema_out += "\n".join(fk_list)
    schema_out += "\n\nSET FOREIGN_KEY_CHECKS = 1;\n"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(schema_out)
    print("Done.")

if __name__ == "__main__":
    convert_mssql_to_mysql()
