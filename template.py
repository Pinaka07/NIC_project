import os

folders=[
    "project/config",
    "project/users",
    "project/users/migrations",
    "project/media/profiles",
    "project/static",
    "project/templates"
]

files=[
    "project/manage.py",
    "project/requirements.txt",

    "project/config/__init__.py",
    "project/config/settings.py",
    "project/config/urls.py",
    "project/config/asgi.py",
    "project/config/wsgi.py",

    "project/users/__init__.py",
    "project/users/admin.py",
    "project/users/apps.py",
    "project/users/models.py",
    "project/users/serializers.py",
    "project/users/permissions.py",
    "project/users/views.py",
    "project/users/urls.py",
    "project/users/tests.py",
    "project/users/signals.py",

    "project/users/migrations/__init__.py"
]

for folder in folders:
    os.makedirs(folder,exist_ok=True)
    print(f"Created Folder: {folder}")

for file in files:
    with open(file,'w') as f:
        pass
    print(f"Created File: {file}")

print("\nProject structure created successfully")