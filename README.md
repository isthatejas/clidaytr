# CLI DayTr
Python-based Kanban board CLI for managing daily tasks using YAML files.


## Introduction
I.  Core Functionality:
- Implements a Kanban board with three core statuses: Todo, In Progress, and Done.
- Enables adding, removing, and moving tasks between these statuses using a CLI.

II. Advanced Features:
- Expands the board with additional status fields (e.g., Backlog).
- Supports managing multiple Kanban boards for various projects (named using commands).
- Introduces task priorities (High, Medium, Low) and facilitates sorting based on priority.
## Deployment

To deploy this project run the code below to get the package installed

```bash
  pip install --editable .
```
Once installed, run the following command to configure the YAML file. The project runs on the basis of the initalized items in the YAML file, which gets stored in the HOME directory.
```bash
  clidaytr configure
```
or 
```bash
  dt configure
```
YAML file initialization variables:
```yaml
---
clidaytr_data: /Users/tejas/.clidaytr.dat
limits:
  todo: 10
  wip: 3
  done: 10
  taskname: 40
repaint: false
```
_____________________

## Commands
Add a task "Task-1" in table-1 with priority high
```bash
  dt add "task-1" -n "table-1" --priority "high"
```
Promote the task with id (here 1)
```bash
  dt promote 1
```
Regress (demote) the task with id (here 1)
```bash
  dt regress 1
```
Delete the task with id (here 1)
```bash
  dt delete 1
```
Show table-2
```bash
  dt show -n "table-2"
```
## Screenshots
![Screenshot 2024-04-12 140639](https://github.com/isthatejas/clidaytr/assets/110784066/dddc0a7d-2d54-47e3-8b88-2cc30fd379f3)


![Screenshot 2024-04-12 141115](https://github.com/isthatejas/clidaytr/assets/110784066/7c1dbdfc-f5b9-4ff0-8f7a-0974fe7dc875)


![Screenshot 2024-04-12 141238](https://github.com/isthatejas/clidaytr/assets/110784066/8dab2af8-e936-4b64-acce-a72386181e10)


