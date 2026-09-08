function updateClock() {
    // Create a new Date object to get the current date and time
    var currentTime = new Date();

    // Format the time as a readable string
    // You can customize the formatting further (e.g., 12-hour format, specific time zones)
    var dateTimeString = currentTime.toLocaleTimeString();

    // Get the element by its ID and update its HTML content
    document.getElementById("display_time").innerHTML = dateTimeString;
}

// Call the function once when the page loads
updateClock();

// Update the clock every second (1000 milliseconds)
setInterval(updateClock, 1000);
