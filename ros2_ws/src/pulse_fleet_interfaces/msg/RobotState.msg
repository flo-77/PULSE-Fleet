string robot_id
string session_id
uint64 sequence_number

float64 position_x
float64 position_y
float64 battery_percentage

string operating_status
string current_task_id
std_msgs/Header header

uint8 HEARTBEAT=0
uint8 STATE_CHANGE=1
uint8 update_type