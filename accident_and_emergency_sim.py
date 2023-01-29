import simpy
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import names

"""
In this simulation we are interested in measuring patient queue times given an arrival rate and capacity of the A&E department. 

We will use real NHS data to model accident and emergency visits.

We will create a synthetic population of people. 

Each person will have a probability of visiting the A&E department.

We will model the A&E department as a resource with a capacity of 10.

We will model the time spent in the A&E department as a random variable with a mean of 2 hours and a standard deviation of 1 hour.

We will model the time between visits as a random variable with a mean of 1 hour and a standard deviation of 0.5 hours.

We will model the time between arrivals as a random variable with a mean of 1 hour and a standard deviation of 0.5 hours.
"""


# Statistics from NHS England
# https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2023/01/Statistical-commentary-December-2022-cftre1.pdf
december_2022_attendence = 2283000
uk_population = 67100000
mean_monthly_attendence_per_person = december_2022_attendence / uk_population
seconds_in_month = 60 * 60 * 24 * (365 / 12)

# Data to save
patient_wait_time_data = {"patient_name": [], "admittance_time_days":[], "wait_time_hrs": []}
accident_and_emergency_queue_data = {"queue_length": [], "admittance_time_days": []}

class AccidentEmergencyDepartment():

    def __init__(self, env, capacity):
        self.env = env
        self.attendance_capacity = simpy.Resource(env=env, capacity=capacity)
        self.waiting_room = []

    def process_patient(self, patient):
        """
        Process a patient.

        Parameters:
            patient (Patient): The patient to process.
        """
        patient_arrival_time = self.env.now
        # patient waits in waiting room
        self.waiting_room.append(patient)

        # Good time now to record the accident and emergency queue length
        accident_and_emergency_queue_data["queue_length"].append(len(self.waiting_room))
        accident_and_emergency_queue_data["admittance_time_days"].append(self.env.now/3600/24)

        # patient waits in attendance_capacity
        attendance_request = self.attendance_capacity.request()
        yield attendance_request # yield statement means that the code will pause here until the request is granted
        # patient leaves waiting room
        self.waiting_room.remove(patient)
        # patient is seen by doctor
        yield self.env.timeout(np.random.triangular(300, 1200, 3600)) # time in seconds
        # release the attendance_capacity
        self.attendance_capacity.release(attendance_request)
        # patient is then discharged (we can add more complexity another for admissions)
        # patient is discharged
        patient_wait_time = self.env.now - patient_arrival_time
        #print(f"{patient.name} discharged from hospital after {patient_finish_time/3600} hours in A&E. Sim time {self.env.now/(3600*24)} days.")
        patient.live_life()
        # Save data
        patient_wait_time_data["patient_name"].append(patient.name)
        patient_wait_time_data["admittance_time_days"].append(patient_arrival_time/3600/24)
        patient_wait_time_data["wait_time_hrs"].append(patient_wait_time/3600)




class Person():
    def __init__(self, env, name, local_knowledge):
        self.env = env
        self.name = name
        self.local_knowledge = local_knowledge
        self.live_life()

    def live_life(self):
        self.env.process(self.visit_a_and_e())

    def visit_a_and_e(self):
        # patient visits A&E
        time_until_next_health_scare = np.random.exponential(1/mean_monthly_attendence_per_person) * seconds_in_month
        yield self.env.timeout(time_until_next_health_scare) # time in seconds
        #print(f"{self.name} arrived at A&E. Sim time {self.env.now / (3600 * 24)} days.")
        self.env.process(self.local_knowledge["nearest_hospital"].process_patient(patient=self))

local_knowledge = {"nearest_hospital": None}

# Create the environment
env = simpy.Environment()

# Create the A&E department
accident_and_emergency_department = AccidentEmergencyDepartment(env=env, capacity=2)

local_knowledge["nearest_hospital"] = accident_and_emergency_department

# Create the patients
local_population_size = 100000
for person in range(local_population_size):
    name = names.get_full_name()
    #print(f"Creating {name}, person number {person} of {local_population_size}")
    patient = Person(env, name=name, local_knowledge=local_knowledge)

# Run the simulation
env.run(until=seconds_in_month*1)

# Convert data to pandas dataframe
patient_wait_time_data = pd.DataFrame(patient_wait_time_data)
accident_and_emergency_queue_data = pd.DataFrame(accident_and_emergency_queue_data)

# Plot the data with seaborn
sns.scatterplot(data=patient_wait_time_data, x="admittance_time_days", y="wait_time_hrs")
plt.title("Patient wait times")
plt.show()

sns.scatterplot(data=accident_and_emergency_queue_data, x="admittance_time_days", y="queue_length")
plt.title("Accident and emergency queue length")
plt.show()



