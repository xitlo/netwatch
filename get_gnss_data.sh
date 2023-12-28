




#!/bin/bash
#this script enters a Docker container and retrieves latitude and longitude data from a GNSS RTK topic.

# The name of the Docker container.
CONTAINER_NAME="pcar_dfdi"

# The ROS topic to retrieve data from.
GNSS_TOPIC="/mb/sensor/gnss_rtk"

# Number of messages to echo from the ROS topic.
MESSAGE_COUNT=1
# Execute a command in the Docker container to retrieve the full GNSS RTK topic data (removing -it for non-interactive mode).
OUTPUT=$(docker exec $CONTAINER_NAME bash -c "source /root/catkin_ws/install/setup.bash && rostopic echo -n $MESSAGE_COUNT $GNSS_TOPIC")
# Print the full output for debugging purposes.

# Parse the output to extract the latitude and longitude fields.
LATITUDE=$(echo "$OUTPUT" | grep "lat: " | awk '{print $2}')
LONGITUDE=$(echo "$OUTPUT" | grep "lon: " | awk '{print $2}')

# Get the current timestamp
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Print the extracted latitude, longitude, and timestamp values.
echo "$(date +"%Y-%m-%d %H:%M:%S") lat: $LATITUDE"
echo "$(date +"%Y-%m-%d %H:%M:%S") lon: $LONGITUDE"
