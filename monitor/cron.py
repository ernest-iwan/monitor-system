from datetime import time
from .models import Test

def my_cron_job():
    tmp = Test(text='Test')
    tmp.save()