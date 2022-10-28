from celery.schedules import crontab

from config.celery_app import app as celery_app

celery_app.conf.beat_schedule = {
    "askanna.launch_scheduled_jobs": {
        "task": "job.tasks.launch_scheduled_jobs",
        "schedule": crontab(minute="*"),
    },
    "askanna.fix_missed_scheduledjobs": {
        "task": "job.tasks.fix_missed_scheduledjobs",
        "schedule": crontab(minute="1-58/5"),
    },
    "askanna.clean_containers_after_run": {
        "task": "job.tasks.clean_containers_after_run",
        "schedule": crontab(minute="2-58/5"),
    },
    "askanna.clean_dangling_images": {
        "task": "job.tasks.clean_dangling_images",
        "schedule": crontab(hour="*", minute="34"),
    },
    "askanna.delete_runs": {
        "task": "job.tasks.delete_runs",
        "schedule": crontab(minute="3-58/5"),
    },
    "askanna.delete_jobs": {
        "task": "job.tasks.delete_jobs",
        "schedule": crontab(minute="3-58/5"),
    },
    "askanna.delete_projects": {
        "task": "project.tasks.delete_projects",
        "schedule": crontab(minute="3-58/5"),
    },
    "askanna.delete_workspaces": {
        "task": "workspace.tasks.delete_workspaces",
        "schedule": crontab(minute="3-58/5"),
    },
}
