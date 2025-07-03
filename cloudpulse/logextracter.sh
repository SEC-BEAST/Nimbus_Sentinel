#!/bin/bash

# Define log files where systemd logs will be stored 
LOG_DIR="/var/log/openstack/"
mkdir -p $LOG_DIR

declare -A services=(
    ["keystone"]="keystone.log"
    ["nova-api"]="nova-api.log"
    ["nova-compute"]="nova-compute.log"
    ["glance-api"]="glance-api.log"
    ["glance-registry"]="glance-registry.log"
    ["cinder-api"]="cinder-api.log"
    ["cinder-volume"]="cinder-volume.log"
    ["neutron-server"]="neutron-server.log"
    ["neutron-l3-agent"]="neutron-l3-agent.log"
    ["neutron-dhcp-agent"]="neutron-dhcp-agent.log"
    ["neutron-metadata-agent"]="neutron-metadata-agent.log"
    ["horizon"]="horizon.log"
    ["ceilometer-agent"]="ceilometer-agent.log"
    ["heat-api"]="heat-api.log"
    ["heat-engine"]="heat-engine.log"
)

# Extract logs and store them in files
for service in "${!services[@]}"; do
    journalctl -u $service --no-pager --since "10 minutes ago" > "$LOG_DIR/${services[$service]}"
done

echo "Logs extracted successfully to $LOG_DIR"
    
    The script extracts logs of the specified services and stores them in the  /var/log/openstack/  directory. 
    Step 3: Create a systemd service 
    Create a systemd service to run the script at regular intervals. 
    Create a systemd service file named  logextracter.service  in the  /etc/systemd/system/  directory.
