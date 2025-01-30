



# importing the datetime module
import datetime

# Getting todays date and time using now() of datetime
# class
current_date = datetime.datetime.now()

# Printing the current_date as the date object itself.
print("Original date and time object:", current_date)

# Using the strftime() of datetime class
# which takes the components of date as parameter
# %Y - year
# %m - month
# %d - day
# %H - Hours
# %M - Minutes
# %S - Seconds
print("Date and Time in Integer Format:",
      int(current_date.strftime("%Y%m%d%H%M%S")))