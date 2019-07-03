from celery import shared_task


@shared_task
def print_demo():
    # Demo to show periodic tasks are setup correctly
    print('PRINT DEMO')
