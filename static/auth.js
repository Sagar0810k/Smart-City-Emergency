document.addEventListener("DOMContentLoaded", () => {
    // Tab switching functionality
    const tabBtns = document.querySelectorAll(".tab-btn")
    const forms = document.querySelectorAll(".auth-forms form")
  
    tabBtns.forEach((btn) => {
      btn.addEventListener("click", function () {
        // Remove active class from all tabs and forms
        tabBtns.forEach((b) => b.classList.remove("active"))
        forms.forEach((f) => f.classList.remove("active"))
  
        // Add active class to clicked tab and corresponding form
        this.classList.add("active")
        const targetForm = document.getElementById(this.dataset.target)
        targetForm.classList.add("active")
      })
    })
  
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
  })
  
  