document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        eventColor: '#3788d8',
        eventOrder: "start", 
        eventLimit: true, 
        dayMaxEvents: true, 
        editable: true,
        eventDrop: function(info) {
            updateTaskDate(info.event); 
        },
        events: function(fetchInfo, successCallback, failureCallback) {
            fetch('/tasks')
            .then(response => response.json())
            .then(tasks => {
                var events = tasks.map(task => ({
                    id: task.id,
                    title: task.title,
                    start: new Date(task.due_date), 
                    allDay: true,
                    backgroundColor: task.color,
                    borderColor: task.color,
                    extendedProps: {
                        description: task.description
                    }
                }));
                successCallback(events);
            })
            .catch(error => {
                failureCallback(error);
                console.error('Error fetching tasks:', error);
            });
        },
        dateClick: function(info) {
            openModal('new', info.dateStr);
        },
        eventClick: function(info) {
            console.log('Task ID:', info.event.id);
            openModal('edit', info.event);
        }
    });

    function openModal(mode, data) {
        var modal = document.getElementById('taskModal');
        modal.style.display = 'block';

        if (mode === 'edit') {
            document.getElementById('deleteButton').style.display = 'inline';
            document.getElementById('taskTitle').value = data.title;
            document.getElementById('taskDescription').value = data.extendedProps.description;
            document.getElementById('taskColor').value = data.backgroundColor;
            document.getElementById('taskDate').value = data.start.toISOString().substring(0, 10);
            document.getElementById('taskId').value = data.id;
        } else {
            document.getElementById('deleteButton').style.display = 'none';
            document.getElementById('taskForm').reset();
            document.getElementById('taskDate').value = data;
            document.getElementById('taskId').value = '';
        }
    }

    document.querySelector('.close').addEventListener('click', function() {
        document.getElementById('taskModal').style.display = 'none';
    });

    document.getElementById('taskForm').addEventListener('submit', function(event) {
        event.preventDefault();
        submitTaskForm(calendar);
    });

    document.getElementById('deleteButton').addEventListener('click', function() {
        deleteTask(calendar);
    });

    calendar.render();
});

function submitTaskForm(calendar) {
    var title = document.getElementById('taskTitle').value;
    var description = document.getElementById('taskDescription').value;
    var color = document.getElementById('taskColor').value;
    var due_date = document.getElementById('taskDate').value;
    var task_id = document.getElementById('taskId').value;

    var method = task_id ? 'PUT' : 'POST';
    var url = task_id ? `/update_task/${task_id}` : '/add_task';

    if (task_id) {
        var inputDate = new Date(due_date);
        inputDate.setDate(inputDate.getDate() + 1);
        due_date = inputDate.toISOString().substring(0, 10);
    }

    fetch(url, {
        method: method,
        body: JSON.stringify({ title, description, due_date, color }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            calendar.refetchEvents(); 
            document.getElementById('taskModal').style.display = 'none';
            document.getElementById('taskForm').reset();
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}


function updateTaskDate(event) {
    var taskId = event.id;
    var newDate = event.start.toISOString().substring(0, 10); 

    fetch(`/update_task_date/${taskId}`, {
        method: 'PUT',
        body: JSON.stringify({ due_date: newDate }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error updating task date:', data.error);
            event.revert(); 
        } else {
            console.log('Task date updated successfully');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        event.revert(); 
    });
}

function deleteTask(calendar) {
    var task_id = document.getElementById('taskId').value;
    if (!task_id) {
        alert('Keine Task-ID vorhanden.');
        return;
    }
    fetch(`/delete_task/${task_id}`, {
        method: 'DELETE'
    }).then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            calendar.refetchEvents(); 
            document.getElementById('taskModal').style.display = 'none';
        }
    });
}
