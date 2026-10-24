# Unique identifier for the warehouse task
string task_id

# Robot that announced the task
string announcer_id

# Destination coordinates in the warehouse (meters)
float64 goal_x
float64 goal_y

# Time when the task was announced
builtin_interfaces/Time timestamp
