const apiBase = "http://localhost:8000"; // Replace with your backend URL

// Utility function to fetch data from API
const fetchData = async (endpoint) => {
    try {
        const response = await fetch(`${apiBase}${endpoint}`);
        if (!response.ok) throw new Error(`Error: ${response.statusText}`);
        return await response.json();
    } catch (error) {
        console.error("Fetch error:", error);
        return [];
    }
};

// Utility function to send data to API
const sendData = async (endpoint, data, method = "POST") => {
    try {
        const response = await fetch(`${apiBase}${endpoint}`, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error(`Error: ${response.statusText}`);
        return await response.json();
    } catch (error) {
        console.error("Send error:", error);
        return null;
    }
};

// Load events into event lists and dropdowns
const loadEvents = async () => {
    const events = await fetchData("/events/");
    const eventList = document.getElementById("event-list");
    const attendeeEventSelect = document.getElementById("attendee-event");
    const taskEventSelect = document.getElementById("task-event");
    const taskFilterSelect = document.getElementById("task-event-filter");

    eventList.innerHTML = events.map(event => `
        <li class="list-group-item d-flex justify-content-between align-items-center">
            ${event.name}
            <button class="btn btn-sm btn-danger" onclick="deleteEvent(${event.id})">Delete</button>
        </li>
    `).join("");

    const eventOptions = events.map(event => `<option value="${event.id}">${event.name}</option>`).join("");
    attendeeEventSelect.innerHTML = eventOptions;
    taskEventSelect.innerHTML = eventOptions;
    taskFilterSelect.innerHTML = `<option value="">All</option>` + eventOptions;
};

// Load attendees into attendee list
const loadAttendees = async () => {
    const attendees = await fetchData("/attendees/");
    const attendeeList = document.getElementById("attendee-list");

    attendeeList.innerHTML = attendees.map(attendee => `
        <li class="list-group-item d-flex justify-content-between align-items-center">
            ${attendee.name} (${attendee.email}) - Event: ${attendee.event_name}
            <button class="btn btn-sm btn-danger" onclick="deleteAttendee(${attendee.id})">Delete</button>
        </li>
    `).join("");
};

// Load tasks into task list
const loadTasks = async (filterEventId = null) => {
    // Fetch tasks based on event ID
    const tasks = await fetchData(`/tasks/${filterEventId ? filterEventId : ''}`);
    
    if (!tasks || tasks.length === 0) {
        console.log("No tasks found");
        return;
    }

    const taskList = document.getElementById("task-list");
    taskList.innerHTML = tasks.map(task => `
        <li class="list-group-item d-flex justify-content-between align-items-center">
            ${task.name} - Deadline: ${task.deadline} - Assignee: ${task.assignee}
            <span class="badge ${task.status === 'Completed' ? 'bg-success' : 'bg-warning'}">
                ${task.status}
            </span>
            <button class="btn btn-sm btn-primary" onclick="toggleTaskStatus(${task.id}, '${task.status}')">
                Mark as ${task.status === 'Completed' ? 'Pending' : 'Completed'}
            </button>
            <button class="btn btn-sm btn-danger" onclick="deleteTask(${task.id})">Delete</button>
        </li>
    `).join("");
};

// Toggle task status
const toggleTaskStatus = async (taskId, currentStatus) => {
    const newStatus = currentStatus === "Completed" ? "Pending" : "Completed";
    
    // Send updated status to the backend
    const updatedTask = await sendData(`/tasks/${taskId}/status`, { status: newStatus }, "PUT");
    
    if (updatedTask) {
        // Reload tasks after updating status
        loadTasks(); // This will re-fetch and update the tasks list
    } else {
        alert("Failed to update task status.");
    }
};

// Delete functions
const deleteEvent = async (id) => {
    await sendData(`/events/${id}/`, {}, "DELETE");
    loadEvents();
};

const deleteAttendee = async (id) => {
    await sendData(`/attendees/${id}/`, {}, "DELETE");
    loadAttendees();
};

const deleteTask = async (id) => {
    await sendData(`/tasks/${id}/`, {}, "DELETE");
    loadTasks();
};

// Event form submission
document.getElementById("event-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("event-name").value;
    const description = document.getElementById("event-description").value;
    const location = document.getElementById("event-location").value;
    const date = document.getElementById("event-date").value;

    await sendData("/events/", { name, description, location, date });
    e.target.reset();
    loadEvents();
});

// Attendee form submission
document.getElementById("attendee-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("attendee-name").value;
    const email = document.getElementById("attendee-email").value;
    const eventId = document.getElementById("attendee-event").value;

    await sendData("/attendees/", { name, email, event_id: eventId });
    e.target.reset();
    loadAttendees();
});

// Task form submission
document.getElementById("task-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("task-name").value;
    const deadline = document.getElementById("task-deadline").value;
    const eventId = document.getElementById("task-event").value;
    const assignee = document.getElementById("task-assignee").value;

    await sendData("/tasks/", { name, deadline, event_id: eventId, assignee });
    e.target.reset();
    loadTasks();
});

// Task filter
document.getElementById("task-event-filter").addEventListener("change", (e) => {
    const eventId = e.target.value;
    loadTasks(eventId);
});

// Initial load
document.addEventListener("DOMContentLoaded", () => {
    loadEvents();
    loadAttendees();
    loadTasks();
});
