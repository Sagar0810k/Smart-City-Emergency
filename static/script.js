document.addEventListener("DOMContentLoaded", () => {
  // Theme toggle functionality
  const themeSwitch = document.getElementById("theme-switch")

  // Check for saved theme preference or use preferred color scheme
  const savedTheme = localStorage.getItem("theme")
  if (savedTheme === "dark") {
    document.body.classList.add("dark")
    themeSwitch.checked = true
  } else if (savedTheme === "light") {
    document.body.classList.remove("dark")
    themeSwitch.checked = false
  } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    document.body.classList.add("dark")
    themeSwitch.checked = true
  }

  themeSwitch.addEventListener("change", function () {
    if (this.checked) {
      document.body.classList.add("dark")
      localStorage.setItem("theme", "dark")
    } else {
      document.body.classList.remove("dark")
      localStorage.setItem("theme", "light")
    }
  })

  // Notification system
  const notification = document.getElementById("notification")
  const notificationMessage = document.getElementById("notification-message")
  const notificationClose = document.getElementById("notification-close")

  function showNotification(message, type = "info") {
    notificationMessage.textContent = message
    notification.className = `notification show ${type}`

    // Auto hide after 5 seconds
    setTimeout(() => {
      hideNotification()
    }, 5000)
  }

  function hideNotification() {
    notification.classList.remove("show")
  }

  notificationClose.addEventListener("click", hideNotification)

  // Report incident form
  const reportForm = document.getElementById("report-form")
  if (reportForm) {
    reportForm.addEventListener("submit", (e) => {
      e.preventDefault()
      const location = document.getElementById("incident-location").value
      const summary = document.getElementById("incident-summary").value

      fetch("/report_incident", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ location, summary }),
      })
        .then((response) => response.json())
        .then((data) => {
          showNotification(data.message, "success")
          reportForm.reset()
        })
        .catch((error) => {
          showNotification("Error reporting incident. Please try again.", "error")
          console.error("Error:", error)
        })
    })
  }

  // Report criminal form
  const criminalForm = document.getElementById("criminal-form")
  if (criminalForm) {
    criminalForm.addEventListener("submit", (e) => {
      e.preventDefault()
      const criminalName = document.getElementById("criminal-name").value
      const location = document.getElementById("criminal-location").value

      fetch("/report_criminal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ criminal_name: criminalName, location: location }),
      })
        .then((response) => response.json())
        .then((data) => {
          showNotification(data.message, "success")
          criminalForm.reset()
        })
        .catch((error) => {
          showNotification("Error reporting criminal activity. Please try again.", "error")
          console.error("Error:", error)
        })
    })
  }
})

// Mark incident as covered
function markAsCovered(incidentId) {
  fetch(`/mark_covered/${incidentId}`, {
    method: "GET",
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        const notification = document.getElementById("notification")
        const notificationMessage = document.getElementById("notification-message")

        notificationMessage.textContent = "Incident marked as covered!"
        notification.className = "notification show success"

        // Auto hide after 3 seconds
        setTimeout(() => {
          notification.classList.remove("show")
          location.reload() // Reload the page to reflect changes
        }, 3000)
      } else {
        const notification = document.getElementById("notification")
        const notificationMessage = document.getElementById("notification-message")

        notificationMessage.textContent = "Error marking incident as covered"
        notification.className = "notification show error"

        // Auto hide after 3 seconds
        setTimeout(() => {
          notification.classList.remove("show")
        }, 3000)
      }
    })
}

