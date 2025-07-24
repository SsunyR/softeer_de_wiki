#!/usr/bin/env python

import os
import sys
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

class HadoopConfigManager:
    def __init__(self):
        # use HADOOP_CONF_DIR variable
        self.config_dir = Path(os.getenv("HADOOP_CONF_DIR", default=".")).resolve()
        
        # Move configurations to instance variable
        self.configurations = {
            "core-site": {
                "fs.defaultFS": "hdfs://localhost:9000",
                "hadoop.tmp.dir": "/tmp/hadoop",
                "yarn.nodemanager.aux-services": "mapreduce_shuffle",
                "yarn.nodemanager.aux-services.mapreduce.shuffle.class": "org.apache.hadoop.mapred.ShuffleHandler"
            },
            "hdfs-site": {
                "dfs.replication": "3",
                "dfs.blocksize": "134217728",
                "dfs.namenode.name.dir": "/hadoop/dfs/name",
                "dfs.datanode.data.dir": "/hadoop/dfs/data"
            },
            "mapred-site": {
                "mapreduce.framework.name": "yarn",
                "mapreduce.jobhistory.address": "localhost:10020",
            },
            "yarn-site": {
                "yarn.resourcemanager.address": "localhost:8032",
            }
        }
    
    def backup_file(self, file_path):
        """Copy file to backup directory (don't move original)"""
        print(f"Backing up {file_path.name}...")
        backup_dir = self.config_dir / "backup"
        if not backup_dir.exists():
            backup_dir.mkdir(parents=True)
        backup_path = backup_dir / f"{file_path.name}.backup"
        shutil.copy2(file_path, backup_path)  # Use copy2 instead of move
        return backup_path

    def find_xml_files(self):
        """Find all XML files in the config directory"""
        if not self.config_dir.exists():
            raise FileNotFoundError(f"Config directory '{self.config_dir}' not found!")
        
        xml_files = list(self.config_dir.glob("*.xml"))
        return xml_files
    
    def update_xml_property(self, file_path, config):
        """Update or add property in XML configuration file"""
        print(f"Modifying {file_path.name}...")
        try:
            # Parse XML file or create new structure if file is empty/invalid
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
            except (ET.ParseError, FileNotFoundError):
                # Create new XML structure
                root = ET.Element("configuration")
                tree = ET.ElementTree(root)
            
            # Iterate through properties and update or add them
            for prop_name, prop_value in config.items():
                property_found = False
                
                # Check if property already exists
                for prop in root.findall('property'):
                    name_elem = prop.find('name')
                    if name_elem is not None and name_elem.text == prop_name:
                        # Update existing property
                        value_elem = prop.find('value')
                        if value_elem is not None:
                            value_elem.text = prop_value
                        else:
                            # Add value element if missing
                            value_elem = ET.SubElement(prop, 'value')
                            value_elem.text = prop_value
                        property_found = True
                        print(f"  Updated property '{prop_name}' in {file_path.name}")
                        break
                
                # Add new property if not found
                if not property_found:
                    new_prop = ET.SubElement(root, 'property')
                    name_elem = ET.SubElement(new_prop, 'name')
                    name_elem.text = prop_name
                    value_elem = ET.SubElement(new_prop, 'value')
                    value_elem.text = prop_value
                    print(f"  Added property '{prop_name}' to {file_path.name}")
            
            # Write back to file with proper formatting
            self.write_xml_with_formatting(tree, file_path)
            
        except ET.ParseError as e:
            print(f"Error parsing XML file {file_path}: {e}")
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
    
    def write_xml_with_formatting(self, tree, file_path):
        """Write XML with proper formatting"""
        try:
            # Convert to string and add proper formatting
            xml_str = ET.tostring(tree.getroot(), encoding='unicode')
            
            # Basic formatting using xml.dom.minidom
            from xml.dom import minidom
            dom = minidom.parseString(xml_str)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                # Write XML declaration and stylesheet
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>\n')
                
                # Write formatted XML (skip the first line which is XML declaration)
                formatted_xml = dom.documentElement.toprettyxml(indent="  ")
                lines = formatted_xml.split('\n')
                # Filter out empty lines and write
                filtered_lines = [line for line in lines if line.strip()]
                f.write('\n'.join(filtered_lines))
                f.write('\n')
                
        except Exception as e:
            print(f"Error writing XML file {file_path}: {e}")
            # Fallback to basic writing
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
    
    def process_configurations(self):
        """Main method to process all configurations"""
        
        try:
            xml_files = self.find_xml_files()
            
            if not xml_files:
                print("No XML files found in config directory")
                return
            
            print(f"Found {len(xml_files)} XML files:")
            for file in xml_files:
                print(f"  - {file.name}")
            print()
            
            # Process each XML file
            for xml_file in xml_files:
                # Get configuration for this file
                file_config = self.configurations.get(xml_file.stem, {})
                
                if not file_config:
                    print(f"No configuration found for {xml_file.name}, skipping...")
                    continue
                
                # Backup original file
                self.backup_file(xml_file)
                
                # Update/add each configuration property
                self.update_xml_property(xml_file, file_config)
            
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Usage: python3 hadoop_config_manager.py")
        print("Uses HADOOP_CONF_DIR environment variable or current directory")
        print()
        return
    
    manager = HadoopConfigManager()
    manager.process_configurations()

if __name__ == "__main__":
    main()