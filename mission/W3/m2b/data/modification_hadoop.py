#!/usr/bin/env python

import os
import sys
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

# use HADOOP_CONF_DIR variable
CONFIG_DIR = Path(os.getenv("HADOOP_CONF_DIR", default=".")).resolve()

# Configurations
CONFIGURATIONS = {
    "core-site": {
        "fs.defaultFS": "hdfs://namenode:9000",
        "hadoop.tmp.dir": "/tmp/hadoop",
        "io.file.buffer.size": "131072",
    },
    "hdfs-site": {
        "dfs.replication": "2",
        "dfs.blocksize": "134217728",
        "dfs.namenode.name.dir": "/hadoop/dfs/name",
    },
    "mapred-site": {
        "mapreduce.framework.name": "yarn",
        "mapreduce.jobhistory.address": "namenode:10020",
        "mapreduce.task.io.sort.mb": "256",
    },
    "yarn-site": {
        "yarn.resourcemanager.address": "namenode:8032",
        "yarn.nodemanager.resource.memory-mb": "8192",
        "yarn.scheduler.minimum-allocation-mb": "1024",
    }
}

def backup_file(file_path):

    print(f"Backing up {file_path.name}...")
    backup_dir = CONFIG_DIR / "backup"
    if not backup_dir.exists():
        backup_dir.mkdir(parents=True)
    backup_path = backup_dir / f"{file_path.name}.backup"
    shutil.copy2(file_path, backup_path)  # Use copy2 instead of move
    return backup_path

def find_xml_files():

    if not CONFIG_DIR.exists():
        raise FileNotFoundError(f"Config directory '{CONFIG_DIR}' not found!")
    
    xml_files = list(CONFIG_DIR.glob("*.xml"))
    return xml_files

def write_xml_with_formatting(tree, file_path):

    try:

        xml_str = ET.tostring(tree.getroot(), encoding='unicode')

        dom = minidom.parseString(xml_str)
        
        with open(file_path, 'w', encoding='utf-8') as f:

            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>\n')
            
            formatted_xml = dom.documentElement.toprettyxml(indent="  ")
            lines = formatted_xml.split('\n')

            filtered_lines = [line for line in lines if line.strip()]
            f.write('\n'.join(filtered_lines))
            f.write('\n')
            
    except Exception as e:
        print(f"Error writing XML file {file_path}: {e}")
        tree.write(file_path, encoding='utf-8', xml_declaration=True)

def update_xml_property(file_path, config):

    print(f"Modifying {file_path.name}...")
    try:
        # Parse XML file or create new structure if file is empty/invalid
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except (ET.ParseError, FileNotFoundError):

            root = ET.Element("configuration")
            tree = ET.ElementTree(root)
        
        for prop_name, prop_value in config.items():
            property_found = False
            
            for prop in root.findall('property'):
                name_elem = prop.find('name')
                if name_elem is not None and name_elem.text == prop_name:
                    
                    value_elem = prop.find('value')
                    if value_elem is not None:
                        value_elem.text = prop_value
                    else:
                        value_elem = ET.SubElement(prop, 'value')
                        value_elem.text = prop_value
                    property_found = True
                    break
            
            if not property_found:
                new_prop = ET.SubElement(root, 'property')
                name_elem = ET.SubElement(new_prop, 'name')
                name_elem.text = prop_name
                value_elem = ET.SubElement(new_prop, 'value')
                value_elem.text = prop_value
        
        write_xml_with_formatting(tree, file_path)
        
    except ET.ParseError as e:
        print(f"Error parsing XML file {file_path}: {e}")
    except Exception as e:
        print(f"Error updating {file_path}: {e}")

def process_configurations():
    
    try:
        xml_files = find_xml_files()
        
        if not xml_files:
            print("No XML files found in config directory")
            return
        
        for xml_file in xml_files:
            file_config = CONFIGURATIONS.get(xml_file.stem, {})
            
            if not file_config:
                print(f"No configuration found for {xml_file.name}, skipping...")
                continue
            
            backup_file(xml_file)
            
            update_xml_property(xml_file, file_config)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def restart_hadoop_services():

    subprocess.run(["stop-dfs.sh"], check=True)
    print("Stopping Hadoop DFS...")
    subprocess.run(["stop-yarn.sh"], check=True)
    print("Stopping Hadoop YARN...")
    subprocess.run(["start-dfs.sh"], check=True)
    print("Starting Hadoop DFS...")
    subprocess.run(["start-yarn.sh"], check=True)
    print("Starting Hadoop YARN...")

def main():
    process_configurations()
    restart_hadoop_services()

if __name__ == "__main__":
    main()